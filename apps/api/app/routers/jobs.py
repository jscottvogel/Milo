import inspect
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.scheduler import scheduler

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

class JobOutput(BaseModel):
    id: str
    name: str
    next_run_time: Optional[str]
    trigger: str

class JobListOutput(BaseModel):
    jobs: List[JobOutput]

@router.get("", response_model=JobListOutput)
async def list_jobs():
    jobs = scheduler.get_jobs()
    job_list = []
    for j in jobs:
        job_list.append(JobOutput(
            id=j.id,
            name=j.name,
            next_run_time=j.next_run_time.isoformat() if j.next_run_time else None,
            trigger=str(j.trigger)
        ))
    return JobListOutput(jobs=job_list)

from fastapi import BackgroundTasks

@router.post("/{job_id}/trigger")
async def trigger_job(job_id: str, background_tasks: BackgroundTasks):
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def run_it():
        try:
            if inspect.iscoroutinefunction(job.func):
                await job.func(*job.args, **job.kwargs)
            else:
                job.func(*job.args, **job.kwargs)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Manual job trigger failed: {e}")

    background_tasks.add_task(run_it)
        
    return {"status": "success", "message": f"Job {job_id} triggered successfully and is running in the background."}
