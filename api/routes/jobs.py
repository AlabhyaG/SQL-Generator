from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_job_repo
from api.models.jobs import JobResult
from repositories.job_repository import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResult)
async def get_job(
    job_id: str,
    job_repo: JobRepository = Depends(get_job_repo),
) -> JobResult:
    data = await job_repo.get(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobResult(**data)
