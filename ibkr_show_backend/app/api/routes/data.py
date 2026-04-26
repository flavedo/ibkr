import logging

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/refresh")
async def trigger_data_refresh() -> dict:
    try:
        import sys
        sys.path.insert(0, "/app/worker")
        from worker.jobs.daily_incremental_job import run_daily_incremental_job
        result = run_daily_incremental_job()
        return {"success": True, "result": result}
    except Exception as e:
        logger.exception("Failed to trigger data refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh data: {str(e)}",
        )
