"""Shared local sentence-transformers embedding utility (Story 2.2).

A generic text -> vector primitive with no knowledge of skills or content.
Sits in core/ (not content/) per AD-8: every feature module may depend on
core/, core/ depends on nothing feature-specific.
"""
import logging
import threading

from huggingface_hub.errors import HfHubHTTPError, LocalEntryNotFoundError
from requests.exceptions import ConnectionError as RequestsConnectionError
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """Lazily load and cache the embedding model as a process-wide singleton."""
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        try:
            _model = SentenceTransformer(MODEL_NAME)
        except (RequestsConnectionError, HfHubHTTPError, LocalEntryNotFoundError) as exc:
            logger.error(
                "ERROR: Embedding model download failed\n"
                "Model: %s (sentence-transformers)\n"
                "Reason: Network error - %s\n\n"
                "Diagnostics:\n"
                "- Check network connectivity: can reach huggingface.co?\n"
                "- Check disk space: at least 100MB free?\n"
                "- Check PyPI access: `pip install sentence-transformers==<version>` manually?\n\n"
                "The application cannot start without the embedding model.",
                MODEL_NAME,
                exc,
            )
            raise
        except OSError as exc:
            logger.error(
                "Embedding model load failed - model file corrupted or checksum mismatch.\n"
                "Model: %s (sentence-transformers)\n"
                "Reason: %s\n\n"
                "Delete cache: ~/.cache/huggingface/hub/models--sentence-transformers--%s and retry.",
                MODEL_NAME,
                exc,
                MODEL_NAME,
            )
            raise
        except Exception as exc:
            logger.exception(
                "ERROR: Embedding model load failed with an unexpected error\n"
                "Model: %s (sentence-transformers)\n"
                "Reason: %s\n\n"
                "The application cannot start without the embedding model.",
                MODEL_NAME,
                exc,
            )
            raise
        logger.info("Embedding model loaded (~100MB memory, %s, %d-dim)", MODEL_NAME, EMBEDDING_DIM)
        return _model


def load_embedding_model() -> None:
    """Eagerly force the embedding model to load and validate its output shape.

    Call once at app startup so a wrong-shape model (AC5) fails fast at boot,
    not on the first real embed_text() call.
    """
    embed_text("startup shape check")


def embed_text(text: str) -> list[float]:
    """Compute a deterministic embedding vector for the given text.

    Loads the model on first use if it hasn't been loaded yet (safe to call
    directly from scripts/tests with no app lifespan running).
    """
    model = _get_model()
    vector = model.encode(text).tolist()
    if len(vector) != EMBEDDING_DIM:
        raise RuntimeError(
            f"Unexpected embedding shape: model produced {len(vector)}-dim vector, "
            f"expected {EMBEDDING_DIM}-dim. Check model name and version match configuration."
        )
    return vector
