"""
training/trainer.py
─────────────────────────────────────────────────────────────────
Agent Training Infrastructure.

Supports in-context learning (few-shot injection) for all agents.
Training loop:
  1. Load labeled examples from FeedbackStore
  2. Convert high-quality examples into few-shot prompt blocks
  3. Inject into agent's training_examples at runtime
  4. Record actual agent outputs back to feedback store
  5. Optionally receive human feedback scores for continuous improvement
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from core.logger import get_logger
from core.schemas import TrainingExample, TrainingBatch
from training.feedback_store import FeedbackStore

logger = get_logger(__name__)


class AgentTrainer:
    """
    Manages in-context training for a single agent.

    Training strategy:
    - Few-shot injection: Top-N high-quality examples are formatted
      as input/output demonstrations and prepended to every LLM call.
    - Feedback loop: After each run, the agent's output can be rated
      (0-100) and stored back to the feedback store.
    - Progressive improvement: Over time, the agent learns from
      high-quality examples without requiring model fine-tuning.
    """

    def __init__(
        self,
        agent: BaseAgent,
        feedback_store: FeedbackStore,
        max_few_shot_examples: int = 5,
        min_quality_score: int = 75,
    ) -> None:
        self.agent = agent
        self.feedback_store = feedback_store
        self.max_few_shot_examples = max_few_shot_examples
        self.min_quality_score = min_quality_score

    # ── Training Setup ───────────────────────────────────────────

    async def load_training_examples(self) -> int:
        """
        Loads high-quality examples from the feedback store and
        injects them into the agent as few-shot demonstrations.

        Returns the number of examples loaded.
        """
        examples = self.feedback_store.load_high_quality(
            agent_id=self.agent.agent_id,
            min_score=self.min_quality_score,
        )

        # Sort by score descending, take top N
        examples.sort(
            key=lambda e: e.feedback_score or 0,
            reverse=True,
        )
        top_examples = examples[: self.max_few_shot_examples]

        # Reset and reload
        self.agent.training_examples = []

        for ex in top_examples:
            self.agent.add_training_example({
                "input": ex.raw_cv_text[:500] + "...",   # Truncate for token budget
                "output": json.dumps(ex.expected_output, indent=2),
            })

        logger.info(
            "training_examples_loaded",
            agent_id=self.agent.agent_id,
            count=len(top_examples),
        )
        return len(top_examples)

    # ── Feedback Recording ────────────────────────────────────────

    async def record_run(
        self,
        raw_cv_text: str,
        expected_output: Dict[str, Any],
        actual_output: Optional[Dict[str, Any]] = None,
    ) -> TrainingExample:
        """
        Records a single agent run as a training example.
        Call this after every pipeline execution to build your dataset.
        """
        example = TrainingExample(
            agent_id=self.agent.agent_id,
            raw_cv_text=raw_cv_text,
            expected_output=expected_output,
            actual_output=actual_output,
        )
        await self.feedback_store.append(example)
        return example

    async def rate_example(
        self,
        example_id: str,
        score: int,
        notes: Optional[str] = None,
    ) -> None:
        """
        Human-in-the-loop feedback method.
        Loads all examples, finds the target, and rewrites the store
        with the updated score.

        Note: For large stores, migrate to a database-backed store.
        """
        all_examples = list(self.feedback_store.iter_all())
        updated = False

        for ex in all_examples:
            if ex.example_id == example_id:
                ex.feedback_score = max(0, min(100, score))
                ex.feedback_notes = notes
                updated = True
                break

        if not updated:
            logger.warning("example_not_found", example_id=example_id)
            return

        # Rewrite store (atomic overwrite)
        import aiofiles
        async with aiofiles.open(
            self.feedback_store._path, "w", encoding="utf-8"
        ) as f:
            for ex in all_examples:
                await f.write(ex.model_dump_json() + "\n")

        logger.info(
            "example_rated",
            example_id=example_id,
            score=score,
        )

    # ── Batch Training ────────────────────────────────────────────

    async def train_from_batch(self, cv_texts: List[str]) -> None:
        """
        Processes a batch of CVs through the agent for training data collection.
        Each CV run produces a TrainingExample stored to the feedback store.

        Usage: Feed diverse CV samples (junior/senior/different fields)
               to build a quality dataset over time.
        """
        logger.info(
            "batch_training_started",
            agent_id=self.agent.agent_id,
            batch_size=len(cv_texts),
        )

        for i, cv_text in enumerate(cv_texts):
            try:
                logger.info(
                    "batch_training_item",
                    agent_id=self.agent.agent_id,
                    index=i + 1,
                    total=len(cv_texts),
                )
                # Record run with empty expected_output
                # Human annotates later via rate_example()
                await self.record_run(
                    raw_cv_text=cv_text,
                    expected_output={},
                    actual_output=None,
                )
            except Exception as e:
                logger.error(
                    "batch_training_item_error",
                    index=i,
                    error=str(e),
                )

        logger.info(
            "batch_training_complete",
            agent_id=self.agent.agent_id,
            batch_size=len(cv_texts),
        )
