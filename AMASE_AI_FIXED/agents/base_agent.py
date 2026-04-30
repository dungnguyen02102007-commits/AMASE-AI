"""
agents/base_agent.py
─────────────────────────────────────────────────────────────────
Abstract base class for all agents.

Design principles:
- Agents are stateless: they receive a SharedStateManager
  and operate on it, writing results back.
- All agents expose a single async entry point: `run()`.
- Pre/post hooks allow transparent logging and observability.
- Training mode injects few-shot examples into the system prompt.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.logger import get_logger
from core.llm_interface import LLMInterface
from core.shared_state import SharedStateManager
from core.schemas import AgentStatus, AgentRunMeta

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all pipeline agents.

    Subclasses must implement:
      - agent_id  (class attribute)
      - _run()    (core logic)
    """

    agent_id: str = "base_agent"

    def __init__(
        self,
        llm: LLMInterface,
        state_manager: SharedStateManager,
        training_examples: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Args:
            llm               : LLM backend (Gemini or Claude).
            state_manager     : Centralized shared state manager.
            training_examples : Few-shot examples for in-context training.
        """
        self.llm = llm
        self.state_manager = state_manager
        self.training_examples: List[Dict[str, Any]] = training_examples or []
        self._logger = get_logger(f"agent.{self.agent_id}")

    # ── Public Entry Point ───────────────────────────────────────

    async def run(self) -> None:
        """
        Main entry point. Wraps _run() with:
          - timing
          - meta tracking (status, timestamps, retries)
          - error catching and state update on failure
        """
        meta = AgentRunMeta(
            agent_id=self.agent_id,
            status=AgentStatus.RUNNING,
            started_at=datetime.now(),
        )

        state = self.state_manager.get()
        state.agent_meta[self.agent_id] = meta

        self._logger.info("agent_started", model=self.llm.get_model_name())
        start = time.monotonic()

        try:
            await self._run()

            elapsed = time.monotonic() - start
            meta.status = AgentStatus.COMPLETED
            meta.completed_at = datetime.now()

            self._logger.info(
                "agent_completed",
                elapsed_seconds=round(elapsed, 2),
            )

        except Exception as e:
            elapsed = time.monotonic() - start
            meta.status = AgentStatus.FAILED
            meta.error = str(e)
            meta.completed_at = datetime.now()

            self._logger.error(
                "agent_failed",
                error=str(e),
                elapsed_seconds=round(elapsed, 2),
            )
            raise

    # ── Abstract Core ────────────────────────────────────────────

    @abstractmethod
    async def _run(self) -> None:
        """
        Implement agent-specific logic here.
        Read from self.state_manager.get() and write results back.
        """
        ...

    # ── Training Support ─────────────────────────────────────────

    def add_training_example(self, example: Dict[str, Any]) -> None:
        """
        Appends a few-shot training example that will be injected
        into the system prompt during the next run.
        """
        self.training_examples.append(example)
        self._logger.info(
            "training_example_added",
            total_examples=len(self.training_examples),
        )

    def _build_few_shot_block(self) -> str:
        """
        Formats all training examples into a prompt-injectable
        few-shot block string.
        """
        if not self.training_examples:
            return ""

        lines = ["\n=== FEW-SHOT TRAINING EXAMPLES ==="]
        for i, example in enumerate(self.training_examples, 1):
            lines.append(f"\n--- Example {i} ---")
            lines.append(f"INPUT:\n{example.get('input', '')}")
            lines.append(f"EXPECTED OUTPUT:\n{example.get('output', '')}")

        lines.append("=== END OF EXAMPLES ===\n")
        return "\n".join(lines)

    # ── Helpers ──────────────────────────────────────────────────

    def _build_messages(
        self,
        system_prompt: str,
        user_content: str,
    ):
        """
        Constructs the message list for LLM invocation.
        Injects few-shot examples into the system prompt block.
        """
        from langchain_core.messages import SystemMessage, HumanMessage

        few_shot = self._build_few_shot_block()
        full_system = system_prompt + few_shot

        return [
            SystemMessage(content=full_system),
            HumanMessage(content=user_content),
        ]
