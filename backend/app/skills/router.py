"""HTTP routes for the skills module.

Empty until Story 6.2 (POST /api/admin/skills, FR-20) and Story 6.3
(PATCH/DELETE /api/admin/skills/{id}, FR-21/22) add the CRUD endpoints --
out of this story's scope. Not yet mounted in app/main.py; that happens
alongside the first real route, matching content_router/dashboard_router's
own first-endpoint precedent.
"""
from fastapi import APIRouter

router = APIRouter()
