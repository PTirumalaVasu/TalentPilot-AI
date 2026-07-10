"""Tests for the core.embedding module (Story 2.2)."""
import logging
import time
from pathlib import Path

import pytest
from huggingface_hub.errors import HfHubHTTPError
from requests.exceptions import ConnectionError as RequestsConnectionError

from app.core import embedding
from app.main import app


@pytest.fixture(autouse=True)
def _reset_model_cache():
    """Ensure each test starts with no cached model, and cleans up after itself."""
    embedding._model = None
    yield
    embedding._model = None


def test_embed_text_returns_384_dim_list_of_floats():
    result = embedding.embed_text("Data Visualization: creating charts and graphs")

    assert isinstance(result, list)
    assert len(result) == embedding.EMBEDDING_DIM == 384
    assert all(isinstance(x, float) for x in result)


def test_embed_text_is_deterministic():
    text = "Python Programming: writing and maintaining Python code"

    first = embedding.embed_text(text)
    second = embedding.embed_text(text)

    assert first == second


def test_embed_text_without_explicit_load_still_works():
    # No load_embedding_model() call first - lazy-load fallback (AC2).
    assert embedding._model is None

    result = embedding.embed_text("SQL & Databases")

    assert len(result) == 384


def test_load_embedding_model_then_embed_text_reuses_cached_instance(monkeypatch):
    load_count = {"n": 0}
    real_init = embedding.SentenceTransformer.__init__

    def counting_init(self, *args, **kwargs):
        load_count["n"] += 1
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(embedding.SentenceTransformer, "__init__", counting_init)

    embedding.load_embedding_model()
    embedding.embed_text("first call")
    embedding.embed_text("second call")

    assert load_count["n"] == 1


def test_embed_text_latency_under_100ms_when_warm():
    embedding.load_embedding_model()  # warm up

    start = time.perf_counter()
    embedding.embed_text("sample")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 100, f"embed_text took {elapsed_ms:.2f}ms, expected under 100ms"


def test_network_failure_is_logged_with_network_specific_message_and_reraised(monkeypatch, caplog):
    def boom(self, *args, **kwargs):
        raise RequestsConnectionError("simulated DNS/network failure")

    monkeypatch.setattr(embedding.SentenceTransformer, "__init__", boom)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RequestsConnectionError):
            embedding.load_embedding_model()

    messages = [record.message for record in caplog.records]
    assert any("Network error" in m for m in messages), messages
    assert not any("corrupted" in m.lower() for m in messages), messages


def test_hf_hub_http_error_is_treated_as_network_failure(monkeypatch, caplog):
    def boom(self, *args, **kwargs):
        raise HfHubHTTPError("simulated HF hub 503")

    monkeypatch.setattr(embedding.SentenceTransformer, "__init__", boom)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(HfHubHTTPError):
            embedding.load_embedding_model()

    messages = [record.message for record in caplog.records]
    assert any("Network error" in m for m in messages), messages


def test_corrupted_cache_failure_is_logged_with_delete_cache_message_and_reraised(monkeypatch, caplog):
    def boom(self, *args, **kwargs):
        raise OSError("simulated corrupted cache file")

    monkeypatch.setattr(embedding.SentenceTransformer, "__init__", boom)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(OSError):
            embedding.load_embedding_model()

    messages = [record.message for record in caplog.records]
    assert any("corrupted" in m.lower() and "delete cache" in m.lower() for m in messages), messages
    assert not any("Network error" in m for m in messages), messages


def test_wrong_output_shape_raises_runtime_error(monkeypatch):
    class _FakeVector:
        def tolist(self):
            return [0.0] * 768  # wrong dimension, expected 384

    class _FakeModel:
        def encode(self, text):
            return _FakeVector()

    monkeypatch.setattr(embedding, "_get_model", lambda: _FakeModel())

    with pytest.raises(RuntimeError, match="384"):
        embedding.embed_text("sample")


def test_load_embedding_model_fails_fast_on_wrong_shape_at_startup_not_first_request(monkeypatch):
    """AC5: a wrong-shape model must fail at load_embedding_model() (startup), not
    silently succeed until the first real embed_text() call from a request/job."""
    class _FakeVector:
        def tolist(self):
            return [0.0] * 768

    class _FakeModel:
        def encode(self, text):
            return _FakeVector()

    monkeypatch.setattr(embedding.SentenceTransformer, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(embedding, "_get_model", lambda: _FakeModel())

    with pytest.raises(RuntimeError, match="384"):
        embedding.load_embedding_model()


def test_concurrent_first_access_loads_model_exactly_once(monkeypatch):
    """Two threads racing _get_model() before the model is loaded must not
    double-instantiate SentenceTransformer. With the lock in place, the second
    thread blocks on the lock (never entering __init__ concurrently) rather
    than racing past the `if _model is None` check."""
    import threading
    import time as time_module

    load_count = {"n": 0}
    real_init = embedding.SentenceTransformer.__init__

    def slow_counting_init(self, *args, **kwargs):
        load_count["n"] += 1
        time_module.sleep(0.2)  # widen the window a racing caller could exploit
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(embedding.SentenceTransformer, "__init__", slow_counting_init)

    results = []

    def worker():
        results.append(embedding.embed_text("race condition probe"))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert load_count["n"] == 1
    assert len(results) == 2


def test_no_router_file_calls_embed_text_directly():
    """AC4: embed_text must never be called from a request-handling path.
    Regression guard for a future PR accidentally wiring it into a router."""
    backend_app_dir = Path(__file__).resolve().parent.parent / "app"
    router_files = list(backend_app_dir.glob("*/router.py"))

    assert router_files, "expected to find at least one router.py under backend/app/*/"

    offending = [
        str(f) for f in router_files
        if "embed_text" in f.read_text(encoding="utf-8")
    ]

    assert not offending, f"embed_text() must not be called from router files: {offending}"


@pytest.mark.asyncio
async def test_app_lifespan_warms_the_model_at_startup():
    assert embedding._model is None

    async with app.router.lifespan_context(app):
        # lifespan startup has run by the time we're inside the context
        assert embedding._model is not None
