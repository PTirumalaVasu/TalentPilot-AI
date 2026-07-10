"""Idempotent seed scripts for initial database population."""
import uuid
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from app.auth.models import Account
from app.assignments.models import Employee, Skill
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

    # Load the embedding model (small local model, ~200MB)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    skill_definitions = [
        (SKILL_DATA_VIZ_ID, "Data Visualization", "Creating charts, graphs, and visual representations of data"),
        (SKILL_SALESFORCE_ID, "Salesforce Admin", "Administering Salesforce CRM systems and user management"),
        (SKILL_PYTHON_ID, "Python Programming", "Writing and maintaining Python code and applications"),
        (SKILL_SQL_ID, "SQL & Databases", "Database design, SQL queries, and data management"),
        (SKILL_COMMUNICATION_ID, "Communication Skills", "Effective written and verbal communication"),
    ]

    skills = []
    for skill_id, name, description in skill_definitions:
        embedding = model.encode(f"{name}: {description}").tolist()
        skills.append(
            Skill(
                id=skill_id,
                name=name,
                description=description,
                embedding=embedding,
            )
        )

    session.add_all(skills)
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
    await create_default_accounts(session)
    await session.commit()
