from fastapi import APIRouter, Depends, Response

from api.dependencies import get_session_repo
from api.models.sessions import HistoryEntry, SessionHistory
from repositories.session_repository import SessionRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}/history", response_model=SessionHistory)
async def get_history(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo),
) -> SessionHistory:
    entries = await session_repo.get_history(session_id)
    return SessionHistory(
        session_id=session_id,
        entries=[HistoryEntry(**e) for e in entries],
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo),
) -> Response:
    await session_repo.delete(session_id)
    return Response(status_code=204)
