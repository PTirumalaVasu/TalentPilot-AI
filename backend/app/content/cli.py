"""Manual trigger entrypoint for content ingestion/seeding.

Usage:
    python -m app.content.cli ingest [--skill-id UUID ...]
    python -m app.content.cli seed --skill-id UUID --title ... --url ...
        --type {VIDEO,DOCUMENT,WEBSITE} [--description ...]

Deliberately a CLI, not an HTTP admin endpoint (Story 2.3 Scope Note 6) --
adds zero new authenticated/role-gated route surface. AD-7's batch-only
invariant means this script never touches content/router.py.
"""
import argparse
import asyncio
import sys
import uuid

from app.content import youtube_client
from app.content.schemas import ManualContentCreate
from app.content.service import manual_seed_content, run_ingestion_job
from app.core.config import settings
from app.core.db import async_session_factory


def _open_session():
    return async_session_factory()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="app.content.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Run the YouTube batch ingestion job")
    ingest_parser.add_argument(
        "--skill-id", dest="skill_ids", action="append", type=uuid.UUID, default=None,
        help="Limit ingestion to specific Skill IDs (repeatable). Omit to process all Skills.",
    )

    seed_parser = subparsers.add_parser("seed", help="Manually insert a Content row (no YouTube call)")
    seed_parser.add_argument("--skill-id", dest="skill_id", type=uuid.UUID, required=True)
    seed_parser.add_argument("--title", required=True)
    seed_parser.add_argument("--url", required=True)
    seed_parser.add_argument("--type", dest="type", required=True, choices=["VIDEO", "DOCUMENT", "WEBSITE"])
    seed_parser.add_argument("--description", default=None)

    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    if args.command == "ingest":
        if not settings.YOUTUBE_API_KEY:
            print(
                "ERROR: YOUTUBE_API_KEY is not configured.\n"
                "Set YOUTUBE_API_KEY in backend/.env before running ingestion.\n"
                "See backend/.env.example for the placeholder.",
                file=sys.stderr,
            )
            return 1

        async with _open_session() as session:
            summary = await run_ingestion_job(session, skill_ids=args.skill_ids)

        print(f"Processed {len(summary['processed'])} skill(s).")
        if summary["quota_exhausted"]:
            print(
                f"Quota exhausted; skipped {len(summary['skipped_due_to_quota'])} skill(s). "
                "Retry tomorrow."
            )
        return 0

    if args.command == "seed":
        data = ManualContentCreate(
            skill_id=args.skill_id,
            title=args.title,
            url=args.url,
            type=args.type,
            description=args.description,
        )
        async with _open_session() as session:
            result = await manual_seed_content(session, data=data)

        print(f"Seeded content: {result}")
        return 0

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


def main() -> None:
    args = parse_args(sys.argv[1:])
    exit_code = asyncio.run(run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
