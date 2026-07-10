"""AD-7 regression guard (Story 2.3, AC6): content ingestion must never be
triggered by a live request. Mirrors test_embedding.py's
test_no_router_file_calls_embed_text_directly pattern."""
from pathlib import Path

BACKEND_APP_DIR = Path(__file__).resolve().parent.parent / "app"
FORBIDDEN_SYMBOLS = ("run_ingestion_job", "search_videos")
# youtube_client is ingestion-only end to end (no router has any legitimate
# reason to import it), so banning the whole module is correct there. Unlike
# youtube_client, app.content.service also holds legitimate read-only
# functions real routes need (e.g. match_content_for_skill, Story 3.4) --
# banning the entire module import would false-positive on those, so
# ingestion-from-service is caught via FORBIDDEN_SYMBOLS (which also blocks
# an aliased `from app.content.service import run_ingestion_job as _rij`)
# instead of a blanket import-source ban.
FORBIDDEN_IMPORT_SOURCES = (
    "app.content.youtube_client",
    "app.content import youtube_client",
)


def test_no_router_or_main_file_triggers_ingestion():
    """run_ingestion_job/search_videos must be called only from
    content/cli.py and this story's own tests -- never from any router.py
    or main.py. Also blocks the module-level import (even aliased), since a
    literal-symbol grep alone would miss `from app.content.service import
    run_ingestion_job as _rij; _rij(...)`."""
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
        for source in FORBIDDEN_IMPORT_SOURCES:
            if source in content:
                offending.append(f"{f}: imports from {source}")

    assert not offending, (
        f"Ingestion job must not be called from router/main files (AD-7): {offending}"
    )
