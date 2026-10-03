from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.api.deps import get_current_user, CurrentUser
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobDuplicateCheckRequest
from app.services.job_service import JobService

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/py/jobs", tags=["jobs"])
job_service = JobService()

@router.get("", response_model=List[Dict[str, Any]])
async def get_jobs(current_user: CurrentUser = Depends(get_current_user)):
    return job_service.get_user_jobs(current_user.id)

@router.post("/check-duplicate", response_model=Dict[str, Any])
async def check_duplicate_job(request: JobDuplicateCheckRequest, current_user: CurrentUser = Depends(get_current_user)):
    return job_service.check_duplicate_job(
        user_id=current_user.id,
        title=request.title,
        company=request.company,
        job_url=request.job_url,
        application_url=request.application_url
    )

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job(job_id: str, current_user: CurrentUser = Depends(get_current_user)):
    job = job_service.get_job_by_id(job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, current_user: CurrentUser = Depends(get_current_user)):
    try:
        return job_service.create_job(current_user.id, job_data)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error in create_job route for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save job: {str(e)}")

@router.put("/{job_id}", response_model=Dict[str, Any])
async def update_job(job_id: str, job_data: JobUpdate, current_user: CurrentUser = Depends(get_current_user)):
    try:
        updated = job_service.update_job(job_id, current_user.id, job_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Job not found or update failed")
        return updated
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Error updating job {job_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, current_user: CurrentUser = Depends(get_current_user)):
    success = job_service.delete_job(job_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or delete failed")
    return None

