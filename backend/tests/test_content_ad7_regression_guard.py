"""AD-7 regression guard (Story 2.3, AC6; re-scoped Story 6.6 per the
architecture spine's 2026-09-08 amendment): batch ingestion (the shared
settings.YOUTUBE_API_KEY, run_ingestion_job) must never be triggered by a
live request. Mirrors test_embedding.py's
test_no_router_file_calls_embed_text_directly pattern.

Story 6.6 adds a live, per-admin/org-wide-credential search path
(skills/router.py -> content/service.py::search_content_for_skill ->
youtube_client.search_videos / udemy_client.search_courses) that is
legitimate and must NOT trip this guard -- the boundary this guard
protects was never "no router may reach search_videos", it was "no router
may trigger batch ingestion or read the shared YOUTUBE_API_KEY". The
original, pre-Story-6.6 version of this guard banned the `search_videos`
symbol and any `app.content.youtube_client` import outright, which was
accurate only because no live per-request search path existed yet."""
from pathlib import Path

BACKEND_APP_DIR = Path(__file__).resolve().parent.parent / "app"
FORBIDDEN_SYMBOLS = ("run_ingestion_job", "settings.YOUTUBE_API_KEY")


def test_no_router_or_main_file_triggers_ingestion():
    """run_ingestion_job (batch ingestion) and settings.YOUTUBE_API_KEY
    (the shared batch key) must never appear in any router.py or main.py --
    the live per-admin/org-wide-credential search path (Story 6.6) reaches
    search_videos/udemy_client.search_courses only transitively, through
    content/service.py, and is unaffected by this guard."""
    router_files = list(BACKEND_APP_DIR.glob("*/router.py"))
    main_files = [BACKEND_APP_DIR / "main.py"]

    assert router_files, "expected to find at least one router.py under backend/app/*/"
    assert main_files[0].exists(), "expected backend/app/main.py to exist"

    offending = []
    for f in router_files + main_files:
        content = f.read_text(encoding="utf-8")
        for symbol in FORBIDDEN_SYMBOLS:
            if symbol in content:
                offending.append(f"{f}: {symbol}")

    assert not offending, (
        f"Batch ingestion / the shared YOUTUBE_API_KEY must not be referenced from router/main files (AD-7): {offending}"
    )
