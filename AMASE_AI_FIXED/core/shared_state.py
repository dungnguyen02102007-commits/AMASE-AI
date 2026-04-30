"""
core/shared_state.py
─────────────────────────────────────────────────────────────────
Centralized shared state manager.

Responsibilities:
- Thread-safe + async-safe state mutations via asyncio.Lock
- Persistent storage to disk (JSON) after every update
- Optional Redis-backed distributed state for multi-process setups
- Full audit trail via version increments
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles

from config import Config
from core.logger import get_logger
from core.schemas import SharedState as SharedStateModel, PipelineStage

logger = get_logger(__name__)


class SharedStateManager:
    """
    Manages the lifecycle of the SharedState object.

    Usage:
        manager = SharedStateManager(session_id="abc-123")
        await manager.initialize(raw_cv_text="...")
        state = manager.get()
        await manager.update_stage(PipelineStage.COLLECTING)
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        persist_path: Optional[Path] = None,
    ) -> None:
        self._state: Optional[SharedStateModel] = None
        self._lock = asyncio.Lock()
        self._session_id = session_id

        # Resolve persistence path
        self._persist_path = (
            persist_path
            or Config.SHARED_DATA_DIR / f"state_{session_id or 'default'}.json"
        )

    # ── Initialization ──────────────────────────────────────────

    async def initialize(
        self,
        raw_cv_text: str,
        cv_file_path: Optional[str] = None,
        max_refinement_cycles: int = Config.MAX_REFINEMENT_CYCLES,
    ) -> SharedStateModel:
        """
        Creates a fresh SharedState for a new session.
        Persists it to disk immediately.
        """
        async with self._lock:
            self._state = SharedStateModel(
                session_id=self._session_id or "",
                raw_cv_text=raw_cv_text,
                cv_file_path=cv_file_path,
                max_refinement_cycles=max_refinement_cycles,
            )
            await self._persist()
            logger.info(
                "state_initialized",
                session_id=self._state.session_id,
                version=self._state.version,
            )
            return self._state

    async def load_from_disk(self) -> SharedStateModel:
        """
        Loads a previously saved state from disk.
        Useful for resuming interrupted pipelines.
        """
        async with self._lock:
            if not self._persist_path.exists():
                raise FileNotFoundError(
                    f"No state file found at '{self._persist_path}'."
                )
            async with aiofiles.open(self._persist_path, "r", encoding="utf-8") as f:
                content = await f.read()
            self._state = SharedStateModel.from_json(content)
            logger.info(
                "state_loaded_from_disk",
                session_id=self._state.session_id,
                version=self._state.version,
            )
            return self._state

    # ── Read ────────────────────────────────────────────────────

    def get(self) -> SharedStateModel:
        """Returns the current state object. Read-only access."""
        if self._state is None:
            raise RuntimeError(
                "SharedState is not initialized. Call `initialize()` first."
            )
        return self._state

    # ── Write ───────────────────────────────────────────────────

    async def update_stage(self, stage: PipelineStage) -> None:
        """Updates the pipeline stage and persists."""
        async with self._lock:
            self._state.stage = stage
            self._state.increment_version()
            await self._persist()
            logger.info(
                "state_stage_updated",
                stage=stage.value,
                version=self._state.version,
            )

    async def set_agent1_output(self, output) -> None:
        async with self._lock:
            self._state.agent1_output = output
            self._state.increment_version()
            await self._persist()
            logger.info("state_agent1_output_saved", version=self._state.version)

    async def set_agent2_output(self, output) -> None:
        async with self._lock:
            self._state.agent2_output = output
            self._state.increment_version()
            await self._persist()
            logger.info("state_agent2_output_saved", version=self._state.version)

    async def set_agent3_output(self, output) -> None:
        async with self._lock:
            self._state.agent3_output = output
            self._state.increment_version()
            await self._persist()
            logger.info("state_agent3_output_saved", version=self._state.version)

    async def record_refinement_cycle(self, cycle_data: dict) -> None:
        async with self._lock:
            self._state.refinement_history.append(cycle_data)
            self._state.refinement_cycle += 1
            self._state.increment_version()
            await self._persist()
            logger.info(
                "refinement_cycle_recorded",
                cycle=self._state.refinement_cycle,
            )

    async def set_feedback(self, feedback: dict) -> None:
        async with self._lock:
            self._state.feedback = feedback
            self._state.increment_version()
            await self._persist()
            logger.info("feedback_recorded", version=self._state.version)

    # ── Persistence ─────────────────────────────────────────────

    async def _persist(self) -> None:
        """
        Write the current state to disk as JSON.
        Called internally after every mutation while the lock is held.
        """
        async with aiofiles.open(self._persist_path, "w", encoding="utf-8") as f:
            await f.write(self._state.to_json())
