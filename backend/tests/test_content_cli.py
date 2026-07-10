"""Tests for the content ingestion CLI entrypoint (Story 2.3, AC5/AC6/AC7).

service.run_ingestion_job / manual_seed_content are mocked at module level --
this tests CLI wiring (arg parsing, dispatch, YOUTUBE_API_KEY gate), not
service logic (already covered by test_content_ingestion.py).
"""
import uuid

import pytest

from app.content import cli


@pytest.mark.asyncio
async def test_seed_command_invokes_manual_seed_content_with_parsed_args(monkeypatch):
    """The `seed` subcommand should build a ManualContentCreate from CLI args
    and call manual_seed_content -- never touching youtube_client."""
    skill_id = uuid.uuid4()
    captured = {}

    def fail_if_called(*args, **kwargs):
        raise AssertionError("seed command must never call youtube_client")

    async def fake_manual_seed_content(db, *, data):
        captured["data"] = data
        return object()

    monkeypatch.setattr(cli.youtube_client, "search_videos", fail_if_called)
    monkeypatch.setattr(cli.youtube_client, "get_video_durations", fail_if_called)
    monkeypatch.setattr(cli, "manual_seed_content", fake_manual_seed_content)
    monkeypatch.setattr(cli, "_open_session", lambda: _FakeSessionContext())

    args = cli.parse_args(
        [
            "seed",
            "--skill-id", str(skill_id),
            "--title", "Manual Doc",
            "--url", "https://example.com/doc.pdf",
            "--type", "DOCUMENT",
            "--description", "A manually curated doc",
        ]
    )

    exit_code = await cli.run(args)

    assert exit_code == 0
    assert captured["data"].skill_id == skill_id
    assert captured["data"].title == "Manual Doc"
    assert captured["data"].type == "DOCUMENT"
    assert captured["data"].description == "A manually curated doc"


@pytest.mark.asyncio
async def test_ingest_command_exits_nonzero_without_youtube_api_key(monkeypatch, capsys):
    """AC7: `ingest` must exit non-zero with a clear message when
    YOUTUBE_API_KEY is unset, before making any HTTP call."""
    monkeypatch.setattr(cli.settings, "YOUTUBE_API_KEY", None)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("no HTTP call should be attempted with no API key")

    monkeypatch.setattr(cli.youtube_client, "search_videos", fail_if_called)
    monkeypatch.setattr(cli.youtube_client, "get_video_durations", fail_if_called)

    args = cli.parse_args(["ingest"])

    exit_code = await cli.run(args)

    assert exit_code != 0
    captured = capsys.readouterr()
    assert "YOUTUBE_API_KEY" in captured.out or "YOUTUBE_API_KEY" in captured.err


class _FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False
