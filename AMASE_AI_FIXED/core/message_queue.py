"""
core/message_queue.py
─────────────────────────────────────────────────────────────────
Async message queue layer.

Two backends are supported:
  1. InMemoryQueue  — asyncio.Queue (dev / single-process)
  2. RedisQueue     — Redis Streams (production / distributed)

Both implement the same AsyncQueueInterface so the orchestrator
is completely decoupled from the transport layer.
"""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Optional

from core.logger import get_logger
from core.schemas import QueueMessage
from config import Config

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────
# BASE INTERFACE
# ────────────────────────────────────────────────────────────────

class AsyncQueueInterface(ABC):
    """Unified async interface for all queue backends."""

    @abstractmethod
    async def publish(self, message: QueueMessage) -> None:
        """Publish a message to the queue."""
        ...

    @abstractmethod
    async def consume(self, timeout: float = 30.0) -> Optional[QueueMessage]:
        """
        Consume the next message from the queue.

        Args:
            timeout: Seconds to wait before returning None if queue is empty.

        Returns:
            A QueueMessage or None if timeout is reached.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up connections and resources."""
        ...


# ────────────────────────────────────────────────────────────────
# IN-MEMORY QUEUE (Default / Dev)
# ────────────────────────────────────────────────────────────────

class InMemoryQueue(AsyncQueueInterface):
    """
    asyncio.Queue-backed in-memory message bus.
    Zero dependencies. Suitable for single-process pipelines.
    Falls back automatically when Redis is unavailable.
    """

    def __init__(self, maxsize: int = 0) -> None:
        self._queue: asyncio.Queue[QueueMessage] = asyncio.Queue(maxsize=maxsize)

    async def publish(self, message: QueueMessage) -> None:
        await self._queue.put(message)
        logger.debug(
            "queue_published",
            event_type=message.event_type,
            session_id=message.session_id,
            message_id=message.message_id,
        )

    async def consume(self, timeout: float = 30.0) -> Optional[QueueMessage]:
        try:
            message = await asyncio.wait_for(
                self._queue.get(),
                timeout=timeout,
            )
            logger.debug(
                "queue_consumed",
                event_type=message.event_type,
                session_id=message.session_id,
            )
            return message
        except asyncio.TimeoutError:
            logger.warning("queue_consume_timeout", timeout=timeout)
            return None

    async def close(self) -> None:
        # In-memory queue needs no teardown
        pass

    @property
    def size(self) -> int:
        return self._queue.qsize()


# ────────────────────────────────────────────────────────────────
# REDIS QUEUE (Production / Distributed)
# ────────────────────────────────────────────────────────────────

class RedisQueue(AsyncQueueInterface):
    """
    Redis Streams-backed message queue.
    Enables horizontal scaling across multiple worker processes.
    Requires: redis[hiredis] + aioredis

    Stream key format: cv_system:<event_type>
    Consumer group   : cv_agents
    """

    STREAM_KEY    = "cv_system:events"
    CONSUMER_GROUP = "cv_agents"
    CONSUMER_NAME  = "orchestrator"

    def __init__(self) -> None:
        self._redis = None

    async def _ensure_connection(self) -> None:
        if self._redis is None:
            try:
                import aioredis
                self._redis = await aioredis.from_url(
                    Config.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Ensure consumer group exists
                try:
                    await self._redis.xgroup_create(
                        self.STREAM_KEY,
                        self.CONSUMER_GROUP,
                        id="0",
                        mkstream=True,
                    )
                except Exception:
                    # Group already exists — ignore
                    pass

                logger.info("redis_connected", url=Config.REDIS_URL)
            except Exception as e:
                logger.error("redis_connection_failed", error=str(e))
                raise

    async def publish(self, message: QueueMessage) -> None:
        await self._ensure_connection()
        await self._redis.xadd(
            self.STREAM_KEY,
            {"data": message.model_dump_json()},
        )
        logger.debug(
            "redis_published",
            event_type=message.event_type,
            message_id=message.message_id,
        )

    async def consume(self, timeout: float = 30.0) -> Optional[QueueMessage]:
        await self._ensure_connection()
        timeout_ms = int(timeout * 1000)
        try:
            results = await self._redis.xreadgroup(
                self.CONSUMER_GROUP,
                self.CONSUMER_NAME,
                {self.STREAM_KEY: ">"},
                count=1,
                block=timeout_ms,
            )
            if not results:
                return None

            _, messages = results[0]
            msg_id, fields = messages[0]

            # ACK the message
            await self._redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, msg_id)

            return QueueMessage.model_validate_json(fields["data"])

        except Exception as e:
            logger.error("redis_consume_error", error=str(e))
            return None

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            logger.info("redis_connection_closed")


# ────────────────────────────────────────────────────────────────
# FACTORY
# ────────────────────────────────────────────────────────────────

def create_queue() -> AsyncQueueInterface:
    """
    Returns the appropriate queue backend based on Config.USE_REDIS.
    Falls back to InMemoryQueue if Redis is disabled.
    """
    if Config.USE_REDIS:
        logger.info("queue_backend", backend="redis")
        return RedisQueue()

    logger.info("queue_backend", backend="in_memory")
    return InMemoryQueue()
