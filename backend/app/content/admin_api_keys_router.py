"""HTTP routes for per-admin/org-wide content-source API credentials
(Story 6.5, FR-16, AD-10). Mounted separately from content/router.py (which
owns /api/content) at /api/admin/api-keys -- mirrors the existing
progress/router.py + progress/my_assignments.py precedent of one module
owning two independently-mounted router files.

get_api_keys_status_route is the one place in this module allowed to import
app.assignments.service -- content/service.py and content/repository.py
never do (AD-8: content/ never depends back on assignments/). Resolving the
Udemy "connected by {name}" display name from a raw employee id is the same
router-layer composition auth/router.py::get_me_route already does.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.service import get_employee_by_id_service
from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.content import service as content_service
from app.content.schemas import (
    ApiKeysStatusResponse,
    SetUdemyCredentialRequest,
    SetYoutubeKeyRequest,
    UdemyCredentialStatus,
    YoutubeKeyStatus,
)
from app.core.db import get_db

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=ApiKeysStatusResponse)
async def get_api_keys_status_route(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApiKeysStatusResponse:
    """Configured-or-not status for both credential types (Story 6.5 AC6) --
    never the key/secret value itself."""
    raw = await content_service.get_api_keys_status(session, current_user=current_user)

    configured_by_name = None
    if raw.udemy_configured_by_id is not None:
        employee = await get_employee_by_id_service(session, raw.udemy_configured_by_id)
        configured_by_name = employee.name if employee else None

    return ApiKeysStatusResponse(
        youtube=YoutubeKeyStatus(configured=raw.youtube_configured),
        udemy=UdemyCredentialStatus(
            configured=raw.udemy_configured,
            configured_by=configured_by_name,
            configured_at=raw.udemy_configured_at.isoformat() if raw.udemy_configured_at else None,
        ),
    )


@router.put("/youtube", status_code=status.HTTP_204_NO_CONTENT)
async def set_youtube_key_route(
    request: SetYoutubeKeyRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Saves/replaces the caller's own YouTube key (Story 6.5 AC3)."""
    await content_service.set_youtube_key(session, current_user=current_user, key=request.key)


@router.delete("/youtube", status_code=status.HTTP_204_NO_CONTENT)
async def remove_youtube_key_route(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Removes the caller's own YouTube key (Story 6.5 AC5)."""
    await content_service.remove_youtube_key(session, current_user=current_user)


@router.put("/udemy", status_code=status.HTTP_204_NO_CONTENT)
async def set_udemy_credential_route(
    request: SetUdemyCredentialRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Saves/replaces the single org-wide Udemy credential (Story 6.5 AC4)."""
    await content_service.set_udemy_credential(
        session, current_user=current_user, client_id=request.client_id, client_secret=request.client_secret
    )


@router.delete("/udemy", status_code=status.HTTP_204_NO_CONTENT)
async def remove_udemy_credential_route(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Removes the org-wide Udemy credential (Story 6.5 AC5)."""
    await content_service.remove_udemy_credential(session, current_user=current_user)
