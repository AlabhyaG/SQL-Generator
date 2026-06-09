from fastapi import APIRouter, Depends

from api.dependencies import get_job_repo, get_session_repo
from api.models.query import QueryRequest, QueryResponse
from repositories.job_repository import JobRepository
from repositories.session_repository import SessionRepository
from services.query_service import QueryService

router = APIRouter(prefix="/query", tags=["query"])


def get_query_service(
    job_repo: JobRepository = Depends(get_job_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> QueryService:
    return QueryService(job_repo, session_repo)


@router.post("", response_model=QueryResponse, status_code=202)
async def submit_query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    return await service.submit(request)
