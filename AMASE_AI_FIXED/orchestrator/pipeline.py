"""
orchestrator/pipeline.py
─────────────────────────────────────────────────────────────────
Async Orchestrator — Manages the full multi-agent pipeline.

Execution order:
  1. Agent 1 (Data Collection)
  2. Agent 2 (CV Fixer)
  3. Agent 3 (Evaluator)
  4. Refinement Loop: If Agent 3 says should_refine=True,
     cycle back to Agent 2 -> Agent 3 up to MAX_REFINEMENT_CYCLES

Message queue events are emitted at each stage for observability.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional

from agents.agent1_collector import Agent1DataCollector
from agents.agent2_fixer import Agent2CVFixer
from agents.agent3_evaluator import Agent3Evaluator
from config import Config
from core.llm_interface import LLMFactory
from core.logger import get_logger
from core.message_queue import AsyncQueueInterface, create_queue
from core.schemas import (
    PipelineStage,
    QueueMessage,
    SharedState,
)
from core.shared_state import SharedStateManager
from training.feedback_store import FeedbackStore
from training.trainer import AgentTrainer

logger = get_logger(__name__)


class CVPipelineOrchestrator:
    """
    Async orchestrator for the 3-agent CV analysis pipeline.

    Responsibilities:
    - Constructs and wires up all agents
    - Manages execution order and refinement cycles
    - Emits queue events for observability
    - Exposes training hooks for each agent
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        queue: Optional[AsyncQueueInterface] = None,
    ) -> None:
        self.session_id   = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._queue       = queue or create_queue()
        self._state_mgr   = SharedStateManager(session_id=self.session_id)
        self._feedback_store = FeedbackStore()

        # ── Instantiate LLMs ─────────────────────────────────────
        self._gemini = LLMFactory.create("gemini")
        self._claude = LLMFactory.create("claude")

        # ── Instantiate Agents ───────────────────────────────────
        self._agent1 = Agent1DataCollector(
            llm=self._gemini,
            state_manager=self._state_mgr,
        )
        self._agent2 = Agent2CVFixer(
            llm=self._claude,
            state_manager=self._state_mgr,
        )
        self._agent3 = Agent3Evaluator(
            llm=self._claude,
            state_manager=self._state_mgr,
        )

        # ── Trainers ─────────────────────────────────────────────
        self.trainer1 = AgentTrainer(self._agent1, self._feedback_store)
        self.trainer2 = AgentTrainer(self._agent2, self._feedback_store)
        self.trainer3 = AgentTrainer(self._agent3, self._feedback_store)

    # ── Main Pipeline ────────────────────────────────────────────

    async def run(
        self,
        raw_cv_text: str,
        cv_file_path: Optional[str] = None,
        load_training: bool = True,
    ) -> SharedState:
        """
        Executes the full CV analysis pipeline.

        Args:
            raw_cv_text   : Plain text CV content.
            cv_file_path  : Optional file path (Agent 1 reads if raw_cv_text is empty).
            load_training : Whether to inject stored few-shot examples.

        Returns:
            The final SharedState after all agents have run.
        """
        logger.info(
            "pipeline_started",
            session_id=self.session_id,
        )

        # ── Initialize state ─────────────────────────────────────
        await self._state_mgr.initialize(
            raw_cv_text=raw_cv_text,
            cv_file_path=cv_file_path,
            max_refinement_cycles=Config.MAX_REFINEMENT_CYCLES,
        )

        # ── Load training examples (few-shot injection) ───────────
        if load_training:
            await asyncio.gather(
                self.trainer1.load_training_examples(),
                self.trainer2.load_training_examples(),
                self.trainer3.load_training_examples(),
            )

        # ── Stage 1: Data Collection ──────────────────────────────
        await self._state_mgr.update_stage(PipelineStage.COLLECTING)
        await self._agent1.run()
        await self._emit_event("agent1_done")

        # ── Stage 2: CV Fixing ────────────────────────────────────
        await self._state_mgr.update_stage(PipelineStage.FIXING)
        await self._agent2.run()
        await self._emit_event("agent2_done")

        # ── Stage 3: Evaluation ───────────────────────────────────
        await self._state_mgr.update_stage(PipelineStage.EVALUATING)
        await self._agent3.run()
        await self._emit_event("agent3_done")

        # ── Refinement Loop ───────────────────────────────────────
        await self._run_refinement_loop()

        # ── Finalize ──────────────────────────────────────────────
        await self._state_mgr.update_stage(PipelineStage.COMPLETE)

        state = self._state_mgr.get()
        logger.info(
            "pipeline_complete",
            session_id=self.session_id,
            final_score=state.agent3_output.hire_probability if state.agent3_output else None,
            refinement_cycles=state.refinement_cycle,
        )

        return state

    async def _run_refinement_loop(self) -> None:
        """
        Iterative refinement: if Agent 3 determines the CV score is below
        the threshold, re-run Agent 2 (with updated context) then Agent 3
        until the threshold is met or max cycles is reached.
        """
        state = self._state_mgr.get()

        while (
            state.agent3_output
            and state.agent3_output.should_refine
            and state.refinement_cycle < state.max_refinement_cycles
        ):
            cycle_num = state.refinement_cycle + 1
            logger.info(
                "refinement_cycle_started",
                cycle=cycle_num,
                current_score=state.agent3_output.hire_probability,
            )

            await self._state_mgr.update_stage(PipelineStage.REFINING)

            # Record cycle snapshot
            await self._state_mgr.record_refinement_cycle({
                "cycle": cycle_num,
                "score_before": state.agent3_output.hire_probability,
                "timestamp": datetime.now().isoformat(),
            })

            # Re-run Agent 2 with improvement targets from Agent 3
            await self._agent2.run()
            await self._emit_event("refine_agent2_done", {"cycle": cycle_num})

            # Re-run Agent 3
            await self._agent3.run()
            await self._emit_event("refine_agent3_done", {"cycle": cycle_num})

            # Refresh state reference
            state = self._state_mgr.get()

            logger.info(
                "refinement_cycle_complete",
                cycle=cycle_num,
                new_score=state.agent3_output.hire_probability if state.agent3_output else None,
            )

    # ── Queue Event Emitter ──────────────────────────────────────

    async def _emit_event(
        self,
        event_type: str,
        extra_payload: Optional[dict] = None,
    ) -> None:
        """Publishes a queue event for downstream consumers."""
        msg = QueueMessage(
            session_id=self.session_id,
            event_type=event_type,
            payload=extra_payload or {},
        )
        await self._queue.publish(msg)

    # ── Training API ─────────────────────────────────────────────

    async def submit_feedback(
        self,
        agent_id: str,
        example_id: str,
        score: int,
        notes: Optional[str] = None,
    ) -> None:
        """
        Human feedback submission endpoint.
        Routes to the correct agent trainer.
        """
        trainers = {
            "agent1": self.trainer1,
            "agent2": self.trainer2,
            "agent3": self.trainer3,
        }
        trainer = trainers.get(agent_id)
        if not trainer:
            raise ValueError(f"Unknown agent_id: '{agent_id}'")

        await trainer.rate_example(example_id, score, notes)
        logger.info(
            "feedback_submitted",
            agent_id=agent_id,
            example_id=example_id,
            score=score,
        )

    async def train_from_cv_batch(
        self,
        agent_id: str,
        cv_texts: List[str],
    ) -> None:
        """
        Batch training: Feed multiple CVs to collect training data.
        Human annotates scores later via submit_feedback().
        """
        trainers = {
            "agent1": self.trainer1,
            "agent2": self.trainer2,
            "agent3": self.trainer3,
        }
        trainer = trainers.get(agent_id)
        if not trainer:
            raise ValueError(f"Unknown agent_id: '{agent_id}'")

        await trainer.train_from_batch(cv_texts)

    # ── Cleanup ───────────────────────────────────────────────────

    async def close(self) -> None:
        """Release all held resources (queue connections, etc.)."""
        await self._queue.close()
        logger.info("orchestrator_closed", session_id=self.session_id)
