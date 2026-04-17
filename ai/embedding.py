"""
embedding.py
------------
Generates dense vector embeddings from text using Sentence-BERT.
The model is loaded once and reused across calls (lazy singleton).
"""

from __future__ import annotations

import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Lazy singleton — avoids reloading the model on every call
# ---------------------------------------------------------------------------

_model: "SentenceTransformer | None" = None
MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, good quality, ~80 MB


def _get_model() -> "SentenceTransformer":
    """Load (or return cached) Sentence-BERT model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is not installed.\n"
                "Run: pip install sentence-transformers"
            )
        print(f"[embedding] Loading model '{MODEL_NAME}' (first run only)...")
        _model = SentenceTransformer(MODEL_NAME)
        print("[embedding] Model loaded.")
    return _model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_embedding(text: str) -> np.ndarray:
    """
    Encode a single string into a fixed-size embedding vector.

    Args:
        text: Any text (CV content, job description, etc.)

    Returns:
        1-D numpy array of float32 values.
    """
    model = _get_model()
    # encode() returns a 2-D array for batches; squeeze to 1-D
    vector = model.encode([text], convert_to_numpy=True)[0]
    return vector.astype(np.float32)


def get_embeddings_batch(texts: list[str]) -> list[np.ndarray]:
    """
    Encode multiple strings in a single batched forward pass (faster).

    Args:
        texts: List of strings to encode.

    Returns:
        List of 1-D numpy arrays, one per input string.
    """
    model = _get_model()
    matrix = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return [row.astype(np.float32) for row in matrix]