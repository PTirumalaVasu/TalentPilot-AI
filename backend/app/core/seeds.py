"""Idempotent seed scripts for initial database population."""
import uuid
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Account
from app.assignments.models import ContentCatalog, Employee, Skill
from app.core.embedding import embed_text
from app.core.seed_ids import CASEY_ID, JORDAN_ID, MORGAN_ID, RITA_ID, SAM_ID

SKILL_DATA_VIZ_ID = uuid.UUID("660e8400-e29b-41d4-a716-446655440001")
SKILL_SALESFORCE_ID = uuid.UUID("660e8400-e29b-41d4-a716-446655440002")
SKILL_PYTHON_ID = uuid.UUID("660e8400-e29b-41d4-a716-446655440003")
SKILL_SQL_ID = uuid.UUID("660e8400-e29b-41d4-a716-446655440004")
SKILL_COMMUNICATION_ID = uuid.UUID("660e8400-e29b-41d4-a716-446655440005")


async def seed_employees(session: AsyncSession) -> None:
    """Idempotently seed the employees table with test data."""
    # Check if seeds already exist
    existing = await session.execute(select(Employee).where(Employee.id == RITA_ID))
    if existing.scalar():
        return

    employees = [
        Employee(
            id=RITA_ID,
            name="Rita the Recommender",
            email="rita@sails.example.com",
            role="HR_ADMIN",
        ),
        Employee(
            id=CASEY_ID,
            name="Casey the Continuer",
            email="casey@sails.example.com",
            role="EMPLOYEE",
        ),
        Employee(
            id=MORGAN_ID,
            name="Morgan the Motivated",
            email="morgan@sails.example.com",
            role="EMPLOYEE",
        ),
        Employee(
            id=JORDAN_ID,
            name="Jordan the Juggernaut",
            email="jordan@sails.example.com",
            role="EMPLOYEE",
        ),
        Employee(
            id=SAM_ID,
            name="Sam the Stellar",
            email="sam@sails.example.com",
            role="EMPLOYEE",
        ),
    ]

    session.add_all(employees)
    await session.flush()


async def seed_skills(session: AsyncSession) -> None:
    """Idempotently seed the skills table with semantic embeddings."""
    # Check if seeds already exist
    existing = await session.execute(select(Skill).where(Skill.id == SKILL_DATA_VIZ_ID))
    if existing.scalar():
        return

    skill_definitions = [
        (SKILL_DATA_VIZ_ID, "Data Visualization", "Creating charts, graphs, and visual representations of data"),
        (SKILL_SALESFORCE_ID, "Salesforce Admin", "Administering Salesforce CRM systems and user management"),
        (SKILL_PYTHON_ID, "Python Programming", "Writing and maintaining Python code and applications"),
        (SKILL_SQL_ID, "SQL & Databases", "Database design, SQL queries, and data management"),
        (SKILL_COMMUNICATION_ID, "Communication Skills", "Effective written and verbal communication"),
    ]

    skills = []
    for skill_id, name, description in skill_definitions:
        vector = embed_text(f"{name}: {description}")
        skills.append(
            Skill(
                id=skill_id,
                name=name,
                description=description,
                embedding=vector,
            )
        )

    session.add_all(skills)
    await session.flush()


# Real content, originally pulled live from YouTube via `app.content.cli
# ingest` (Story 2.3) during manual verification on one machine
# (2026-07-11/12) -- committed here so every environment gets the same real,
# already-verified-relevant videos without each one needing its own
# YOUTUBE_API_KEY / network access / search.list quota at setup time.
# Real ingestion via the CLI remains the way to pick up *new* content later;
# this seed only guarantees a working baseline exists everywhere. Embeddings
# are computed fresh at seed time (not stored as literals), matching
# seed_skills()'s pattern and content/service.py's real
# `_build_embedding_text()` format (`f"{title}: {description or ''}"`), so
# they stay correct if the embedding model ever changes.
_CONTENT_SEED_DATA = [
    (
        SKILL_DATA_VIZ_ID,
        "The beauty of data visualization - David McCandless",
        "View full lesson: http://ed.ted.com/lessons/david-mccandless-the-beauty-of-data-visualization David McCandless turns complex ...",
        "5Zg-C8AAIGg",
        "PT18M18S",
    ),
    (
        SKILL_DATA_VIZ_ID,
        "Top 5 Data Visualizations | Insights from Data | Data Analysis with Python | Data Analytics",
        "Here are top 5 visualizations that you can use to summarize any kind of data and get actionable insights. Data Analytics, data ...",
        "GzjUJr5O1Us",
        "PT1M",
    ),
    (
        SKILL_DATA_VIZ_ID,
        "Visualization | Technology and Analytics | Section F | Part 1 | Episode 107",
        "Link for Notes https://drive.google.com/file/d/1aMNZEaXiTWOYNLUzN6xV86WHhkwo1N_y/view?usp=sharing Link for MCQ ...",
        "1JAwBdDXSK4",
        "PT41M20S",
    ),
    (
        SKILL_SALESFORCE_ID,
        "Salesforce Admin Jobs Disappearing or Evolving? | Future of Salesforce Admin Jobs | Salesforce Hulk",
        "Are Salesforce Admin jobs really disappearing? If you're curious about the future of this career path, this video is your ultimate ...",
        "-AxdVMIJJgY",
        "PT4M23S",
    ),
    (
        SKILL_SALESFORCE_ID,
        "How to Pass the Salesforce Admin Exam [Administrator Certification]",
        "Talking through how to pass the Salesforce Admin exam. I share six tips for studying to pass the salesforce certification test.",
        "EBpKgvS8tnY",
        "PT6M42S",
    ),
    (
        SKILL_SALESFORCE_ID,
        "How to Become a Salesforce Administrator in 30 Days | 30 Days Challenge  | Salesforce Training",
        "Book FREE one-on-on Strategy consultation call at Dreamforce ...",
        "qjqItmQDrs8",
        "PT4M15S",
    ),
    (
        SKILL_PYTHON_ID,
        "Learn Python for FREE in 2025",
        "Learn Python for FREE in 2025 #coding #compsci #python #fyp Source: TikTok (individualkex)",
        "q2-pnQffZik",
        "PT22S",
    ),
    (
        SKILL_PYTHON_ID,
        "Python Full Course for Beginners",
        "Learn Python for AI, machine learning, and web development with this beginner-friendly course! Get 6 months of PyCharm ...",
        "_uQrJ0TkZlc",
        "PT6H14M7S",
    ),
    (
        SKILL_PYTHON_ID,
        "Python for Beginners - Learn Coding with Python in 1 Hour",
        "Learn Python basics in just 1 hour! Perfect for beginners interested in AI and coding. ⚡ Plus, get 6 months of PyCharm FREE with ...",
        "kqtD5dpn9C8",
        "PT1H6S",
    ),
    (
        SKILL_SQL_ID,
        "Fastest Way To Learn SQL",
        "1. Understand the Basics - Learn about relational databases and SQL fundamentals. - Familiarize yourself with basic SQL syntax, ...",
        "pKzazzwVEDg",
        "PT11S",
    ),
    (
        SKILL_SQL_ID,
        "SQL Tutorial - Full Database Course for Beginners",
        "In this course, we'll be looking at database management basics and SQL using the MySQL RDBMS. The course is designed for ...",
        "HXV3zeQKqGY",
        "PT4H20M39S",
    ),
    (
        SKILL_SQL_ID,
        "SQL Explained in 100 Seconds",
        "Learn the fundamentals of Structured Query Language SQL! Even though it's over 40 years old, the world's most popular ...",
        "zsjvFFKOm3c",
        "PT2M23S",
    ),
    (
        SKILL_COMMUNICATION_ID,
        "Give me 8 minutes, and I&#39;ll improve your communication skills by 88%...",
        "Improve your communication skills by 88% in 8 minutes... Instagram: @jak.piggott TikTok: @jak.piggott Email: ...",
        "7hr60EumwQ4",
        "PT8M14S",
    ),
    (
        SKILL_COMMUNICATION_ID,
        "13 Years of Communication Skills Knowledge in 53 minutes",
        "In this video I'm sharing my top 10 most powerful communication tips! FREE 3 Part Video Series ...",
        "g0kzHjmvuYQ",
        "PT53M17S",
    ),
    (
        SKILL_COMMUNICATION_ID,
        "30 Day Plan to Master Your Communication [Complete Beginner’s Guide] + FREE Workbook PDF",
        "Download FREE 30 Day Game Plan PDF ➡ https://bit.ly/3ZEHNg3 Whether you're a beginner at improving your communication ...",
        "U40qvUiefQo",
        "PT11M52S",
    ),
]


async def seed_content(session: AsyncSession) -> None:
    """Idempotently seed content_catalog with real, previously-ingested
    YouTube content for the 5 seeded Skills (see _CONTENT_SEED_DATA above).

    Checked per-skill, not globally: a Skill that already has Content (from
    a prior run of this seed, real `app.content.cli ingest`, or a manual
    seed) is skipped, but a sibling Skill with zero Content still gets
    seeded even if Data Visualization already has some. A single
    Data-Viz-only check previously skipped this function for *all* 5
    Skills the moment any one of them had Content, silently leaving the
    others empty on a partially-ingested machine."""
    seed_skill_ids = {row[0] for row in _CONTENT_SEED_DATA}
    existing = await session.execute(
        select(ContentCatalog.skill_id)
        .where(ContentCatalog.skill_id.in_(seed_skill_ids))
        .distinct()
    )
    already_seeded_skills = set(existing.scalars().all())

    # Group seed data by skill_id to seed per-skill
    by_skill = {}
    for skill_id, title, description, video_id, duration in _CONTENT_SEED_DATA:
        if skill_id not in by_skill:
            by_skill[skill_id] = []
        by_skill[skill_id].append((title, description, video_id, duration))

    rows = []
    for skill_id, items in by_skill.items():
        if skill_id in already_seeded_skills:
            continue
        for title, description, video_id, duration in items:
            embedding = embed_text(f"{title}: {description or ''}")
            rows.append(
                ContentCatalog(
                    skill_id=skill_id,
                    title=title,
                    description=description,
                    type="VIDEO",
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    embedding=embedding,
                    source="YOUTUBE",
                    content_metadata={
                        "video_id": video_id,
                        "duration": duration,
                        "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/default.jpg",
                    },
                )
            )

    if rows:
        session.add_all(rows)
        await session.flush()


async def create_default_accounts(session: AsyncSession) -> None:
    """Idempotently create mock local auth credentials for seed employees."""
    # Check if account already exists
    existing = await session.execute(select(Account).where(Account.email == "rita@sails.example.com"))
    if existing.scalar():
        return

    # In a real app, passwords would be hashed with bcrypt or similar
    # For now, use a simple mock hash ("demo123" -> hash)
    accounts = [
        Account(
            id=RITA_ID,
            email="rita@sails.example.com",
            password_hash="$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG",  # bcrypt("demo123")
            role="HR_ADMIN",
        ),
        Account(
            id=CASEY_ID,
            email="casey@sails.example.com",
            password_hash="$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG",
            role="EMPLOYEE",
        ),
        Account(
            id=MORGAN_ID,
            email="morgan@sails.example.com",
            password_hash="$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG",
            role="EMPLOYEE",
        ),
        Account(
            id=JORDAN_ID,
            email="jordan@sails.example.com",
            password_hash="$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG",
            role="EMPLOYEE",
        ),
        Account(
            id=SAM_ID,
            email="sam@sails.example.com",
            password_hash="$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG",
            role="EMPLOYEE",
        ),
    ]

    session.add_all(accounts)
    await session.flush()


async def run_seeds(session: AsyncSession) -> None:
    """Run all seed scripts in order."""
    await seed_employees(session)
    await seed_skills(session)
    await seed_content(session)
    await create_default_accounts(session)
    await session.commit()
