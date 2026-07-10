"""Tests for the batch content ingestion job and manual seed path (Story 2.3).

Live-DB tests reusing conftest.py's db_session fixture (same pattern as
test_content_repository.py/test_content_service.py). YouTube calls are
always mocked at the service layer -- never real HTTP.
"""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Skill
from app.content.repository import list_all_skills, list_content_by_skill
from app.content.schemas import ManualContentCreate
from app.content.service import (
    _build_embedding_text,
    ingest_content_for_skill,
    manual_seed_content,
    run_ingestion_job,
)
from app.content.youtube_client import QuotaExceededError


async def _make_skill(db_session: AsyncSession, name_prefix: str) -> Skill:
    """Commits (not just flushes) so the Skill survives a later
    db.rollback() triggered by a simulated ingestion failure within the
    same shared db_session -- a rollback undoes the whole transaction,
    which would otherwise wipe out an uncommitted sibling Skill too."""
    skill = Skill(
        name=f"{name_prefix} {uuid.uuid4().hex[:8]}",
        description="Test skill for ingestion",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.commit()
    return skill


def _fake_search_results(count: int, prefix: str = "vid") -> list[dict]:
    return [
        {
            "video_id": f"{prefix}{i}",
            "title": f"{prefix} Title {i}",
            "description": f"{prefix} description {i}",
            "thumbnail_url": f"https://img.example.com/{prefix}{i}.jpg",
        }
        for i in range(count)
    ]


@pytest.mark.asyncio
async def test_list_all_skills_returns_seeded_skills(db_session: AsyncSession):
    """list_all_skills should return at least the seeded Skills."""
    skills = await list_all_skills(db_session)

    assert len(skills) >= 5
    assert all(isinstance(s, Skill) for s in skills)


@pytest.mark.asyncio
async def test_ingest_content_for_skill_inserts_new_rows(
    db_session: AsyncSession, monkeypatch
):
    """A successful ingest should insert Content rows with correct
    source/type/content_metadata."""
    skill = await _make_skill(db_session, "Ingestion Skill A")

    monkeypatch.setattr(
        "app.content.service.youtube_client.search_videos",
        lambda api_key, query, max_results: _fake_search_results(2, "abc"),
    )
    monkeypatch.setattr(
        "app.content.service.youtube_client.get_video_durations",
        lambda api_key, video_ids: {vid: "PT10M0S" for vid in video_ids},
    )
    monkeypatch.setattr(
        "app.content.service.embed_text", lambda text: [0.5] * 384
    )

    result = await ingest_content_for_skill(
        db_session, skill_id=skill.id, skill_name=skill.name, api_key="fake-key"
    )

    assert result["ingested"] == 2
    assert result["skipped_duplicate"] == 0

    rows = await list_content_by_skill(db_session, skill.id)
    assert len(rows) == 2
    for row in rows:
        assert row.source == "YOUTUBE"
        assert row.type == "VIDEO"
        assert row.content_metadata["video_id"] in {"abc0", "abc1"}
        assert row.content_metadata["duration"] == "PT10M0S"
        assert "thumbnail_url" in row.content_metadata


@pytest.mark.asyncio
async def test_ingest_content_for_skill_dedupes_on_second_run(
    db_session: AsyncSession, monkeypatch
):
    """Ingesting the same search results twice must not create duplicate rows."""
    skill = await _make_skill(db_session, "Ingestion Skill Dedup")

    monkeypatch.setattr(
        "app.content.service.youtube_client.search_videos",
        lambda api_key, query, max_results: _fake_search_results(1, "dup"),
    )
    monkeypatch.setattr(
        "app.content.service.youtube_client.get_video_durations",
        lambda api_key, video_ids: {vid: "PT5M0S" for vid in video_ids},
    )
    monkeypatch.setattr(
        "app.content.service.embed_text", lambda text: [0.5] * 384
    )

    first = await ingest_content_for_skill(
        db_session, skill_id=skill.id, skill_name=skill.name, api_key="fake-key"
    )
    second = await ingest_content_for_skill(
        db_session, skill_id=skill.id, skill_name=skill.name, api_key="fake-key"
    )

    assert first["ingested"] == 1
    assert second["ingested"] == 0
    assert second["skipped_duplicate"] == 1

    rows = await list_content_by_skill(db_session, skill.id)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_run_ingestion_job_stops_remaining_skills_on_quota_exceeded(
    db_session: AsyncSession, monkeypatch
):
    """When search_videos raises QuotaExceededError partway through a
    multi-skill run, the job must stop immediately and report which skills
    were skipped due to quota."""
    skill_a = await _make_skill(db_session, "Quota Skill A")
    skill_b = await _make_skill(db_session, "Quota Skill B")
    # Capture names before the call: a rollback() on the shared session
    # (triggered by skill_b's QuotaExceededError) expires ORM attributes,
    # so accessing skill_a/skill_b.name afterward would trigger an
    # out-of-greenlet lazy reload.
    skill_a_name = skill_a.name
    skill_b_name = skill_b.name

    def fake_search(api_key, query, max_results):
        if query == skill_a_name:
            return _fake_search_results(1, "qa")
        raise QuotaExceededError("quota exhausted")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", fake_search)
    monkeypatch.setattr(
        "app.content.service.youtube_client.get_video_durations",
        lambda api_key, video_ids: {vid: "PT1M0S" for vid in video_ids},
    )
    monkeypatch.setattr("app.content.service.embed_text", lambda text: [0.5] * 384)
    monkeypatch.setattr("app.content.service.settings.YOUTUBE_API_KEY", "fake-key")

    summary = await run_ingestion_job(db_session, skill_ids=[skill_a.id, skill_b.id])

    assert summary["quota_exhausted"] is True
    assert skill_a_name in [p["skill_name"] for p in summary["processed"]]
    assert skill_b_name in summary["skipped_due_to_quota"]


@pytest.mark.asyncio
async def test_run_ingestion_job_continues_after_non_quota_skill_failure(
    db_session: AsyncSession, monkeypatch
):
    """A non-quota failure for one skill (e.g. get_video_durations raising)
    must be caught, logged, and the job must continue to the next skill."""
    skill_a = await _make_skill(db_session, "Failing Skill A")
    skill_b = await _make_skill(db_session, "Succeeding Skill B")
    # Capture names before the call: run_ingestion_job's rollback() on the
    # shared session expires ORM attributes, so skill_a/skill_b.name would
    # trigger an out-of-greenlet lazy reload if accessed afterward.
    skill_a_name = skill_a.name
    skill_b_name = skill_b.name

    def fake_search(api_key, query, max_results):
        prefix = "fa" if query == skill_a_name else "fb"
        return _fake_search_results(1, prefix)

    def fake_durations(api_key, video_ids):
        if "fa0" in video_ids:
            raise Exception("simulated videos.list failure")
        return {vid: "PT2M0S" for vid in video_ids}

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", fake_search)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", fake_durations)
    monkeypatch.setattr("app.content.service.embed_text", lambda text: [0.5] * 384)
    monkeypatch.setattr("app.content.service.settings.YOUTUBE_API_KEY", "fake-key")

    summary = await run_ingestion_job(db_session, skill_ids=[skill_a.id, skill_b.id])

    assert summary["quota_exhausted"] is False
    processed_names = [p["skill_name"] for p in summary["processed"]]
    assert skill_b_name in processed_names
    # skill_a failed, so it is not in "processed" as a success
    assert skill_a_name not in processed_names


def test_build_embedding_text_truncates_long_input(monkeypatch):
    """_build_embedding_text must truncate to 1000 chars before embed_text
    ever sees the string."""
    long_description = "x" * 5000

    result = _build_embedding_text("Title", long_description)

    assert len(result) == 1000
    assert result.startswith("Title:")


def test_build_embedding_text_handles_none_description():
    result = _build_embedding_text("Just A Title", None)

    assert result == "Just A Title: "


@pytest.mark.asyncio
async def test_manual_seed_content_never_calls_youtube_client(
    db_session: AsyncSession, monkeypatch
):
    """manual_seed_content must never import/call anything from
    youtube_client -- AC5's own requirement."""
    skill = await _make_skill(db_session, "Manual Seed Skill")

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("youtube_client must never be called by manual_seed_content")

    monkeypatch.setattr(
        "app.content.service.youtube_client.search_videos", _fail_if_called
    )
    monkeypatch.setattr(
        "app.content.service.youtube_client.get_video_durations", _fail_if_called
    )
    monkeypatch.setattr("app.content.service.embed_text", lambda text: [0.3] * 384)

    data = ManualContentCreate(
        skill_id=skill.id,
        title="Manually Curated Doc",
        url="https://example.com/manual-doc.pdf",
        type="DOCUMENT",
        description="A manually curated resource",
    )

    result = await manual_seed_content(db_session, data=data)

    assert result.title == "Manually Curated Doc"
    assert result.source == "MANUAL"
    assert result.type == "DOCUMENT"

    rows = await list_content_by_skill(db_session, skill.id)
    assert len(rows) == 1
