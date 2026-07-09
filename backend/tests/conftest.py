import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://talentpilot:talentpilot@localhost:5432/talentpilot")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")
