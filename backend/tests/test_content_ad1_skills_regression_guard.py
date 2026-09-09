"""AD-1/AD-11 regression guard (Story 6.1): `content/` must never again
import `Skill` or query the `skills` table directly -- both of `content/`'s
former direct-access exceptions (`list_all_skills()`, `get_skill_embedding()`)
were retired in favor of `skills.service` calls by this story. Mirrors
test_content_ad7_regression_guard.py's static-grep pattern."""
from pathlib import Path

CONTENT_APP_DIR = Path(__file__).resolve().parent.parent / "app" / "content"
FORBIDDEN_SNIPPETS = (
    "import Skill",  # covers `from app.skills.models import Skill` and
                      # the retired `from app.assignments.models import Skill`
    "select(Skill",
)


def test_content_module_never_imports_or_queries_skill_directly():
    """Every content/*.py file must be free of direct `Skill`/`skills`-table
    access -- cross-module reads go through `skills.service` only (AD-1)."""
    content_files = list(CONTENT_APP_DIR.glob("*.py"))
    assert content_files, "expected to find at least one .py file under backend/app/content/"

    offending = []
    for f in content_files:
        text = f.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                offending.append(f"{f.name}: contains {snippet!r}")

    assert not offending, (
        f"content/ must never import Skill or query the skills table directly (AD-1/AD-11): {offending}"
    )


def test_content_service_calls_skills_service_not_a_retired_repository_function():
    """The two functions this story retired (`list_all_skills`,
    `get_skill_embedding`) must not exist in content/repository.py, and
    content/service.py must reach their replacements via `skills_service.*`."""
    repository_text = (CONTENT_APP_DIR / "repository.py").read_text(encoding="utf-8")
    service_text = (CONTENT_APP_DIR / "service.py").read_text(encoding="utf-8")

    assert "def list_all_skills" not in repository_text
    assert "def get_skill_embedding" not in repository_text
    assert "skills_service.list_all_skills" in service_text
    assert "skills_service.get_skill_embedding" in service_text
