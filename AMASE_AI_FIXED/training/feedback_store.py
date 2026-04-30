"""
training/feedback_store.py
─────────────────────────────────────────────────────────────────
Persistent feedback store for agent training data.

Uses append-only JSONL format for:
- Auditability
- Streaming reads
- No data loss on crash
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, List, Optional

import aiofiles

from config import Config
from core.logger import get_logger
from core.schemas import TrainingExample, TrainingBatch

logger = get_logger(__name__)


class FeedbackStore:
    """
    Append-only JSONL-backed feedback store.
    One training example per line for efficient streaming.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or Config.FEEDBACK_STORE_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # ── Write ────────────────────────────────────────────────────

    async def append(self, example: TrainingExample) -> None:
        """Append a single training example to the store."""
        async with aiofiles.open(self._path, "a", encoding="utf-8") as f:
            await f.write(example.model_dump_json() + "\n")
        logger.info(
            "feedback_appended",
            example_id=example.example_id,
            agent_id=example.agent_id,
        )

    async def append_batch(self, batch: TrainingBatch) -> None:
        """Append a batch of training examples atomically."""
        async with aiofiles.open(self._path, "a", encoding="utf-8") as f:
            for example in batch.examples:
                await f.write(example.model_dump_json() + "\n")
        logger.info(
            "feedback_batch_appended",
            batch_id=batch.batch_id,
            count=len(batch.examples),
        )

    # ── Read ─────────────────────────────────────────────────────

    def iter_all(self) -> Iterator[TrainingExample]:
        """Synchronous streaming iterator over all stored examples."""
        if not self._path.exists():
            return

        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield TrainingExample.model_validate_json(line)
                    except Exception as e:
                        logger.warning("feedback_parse_error", error=str(e))

    def load_by_agent(self, agent_id: str) -> List[TrainingExample]:
        """Load all examples for a specific agent."""
        return [e for e in self.iter_all() if e.agent_id == agent_id]

    def load_high_quality(
        self,
        agent_id: str,
        min_score: int = 70,
    ) -> List[TrainingExample]:
        """
        Load training examples with feedback_score >= min_score.
        Used to seed few-shot examples for the agent.
        """
        return [
            e for e in self.iter_all()
            if e.agent_id == agent_id
            and e.feedback_score is not None
            and e.feedback_score >= min_score
        ]

    def count(self) -> int:
        if not self._path.exists():
            return 0
        with open(self._path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
