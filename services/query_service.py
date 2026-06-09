import uuid

from fastapi import HTTPException

from api.models.query import QueryRequest, QueryResponse
from repositories.job_repository import JobRepository
from repositories.session_repository import SessionRepository


class QueryService:

    def __init__(self, job_repo: JobRepository, session_repo: SessionRepository) -> None:
        self._job_repo = job_repo
        self._session_repo = session_repo

    async def submit(self, request: QueryRequest) -> QueryResponse:
        job_id = str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())

        db_url = await self._resolve_db_url(request.db_url, session_id)

        await self._job_repo.create(job_id, request.question, session_id)
        await self._job_repo.enqueue(
            job_id=job_id,
            session_id=session_id,
            question=request.question,
            db_url=db_url,
            feedback=request.feedback,
        )

        return QueryResponse(job_id=job_id, session_id=session_id)

    async def _resolve_db_url(self, db_url: str | None, session_id: str) -> str:
        if db_url:
            await self._session_repo.save_db_url(session_id, db_url)
            return db_url

        stored = await self._session_repo.get_db_url(session_id)
        if stored:
            return stored

        raise HTTPException(
            status_code=422,
            detail="db_url is required for new sessions. "
                   "Provide it once and it will be remembered for this session.",
        )
