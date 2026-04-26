import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/refresh")
async def trigger_data_refresh() -> dict:
    try:
        import sys
        sys.path.insert(0, "/app")
        from worker.jobs.daily_incremental_job import run_daily_incremental_job
        result = run_daily_incremental_job()
        return {"success": True, "result": result}
    except Exception as e:
        logger.exception("Failed to trigger data refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh data: {str(e)}",
        )


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV",
        )

    try:
        with tempfile.NamedTemporaryFile(prefix="ibkr_import_", suffix=".csv", delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        try:
            import sys
            sys.path.insert(0, "/app")
            from worker.clients.es_client import ElasticsearchWriter
            from worker.jobs.import_daily_snapshot import import_daily_snapshot_file

            es_host = os.getenv("ES_HOST", "http://elasticsearch:9200")
            es_user = os.getenv("ES_USERNAME", "")
            es_pass = os.getenv("ES_PASSWORD", "")
            verify_certs = os.getenv("ES_VERIFY_CERTS", "false").lower() == "true"

            es_writer = ElasticsearchWriter(
                es_host=es_host,
                username=es_user,
                password=es_pass,
                verify_certs=verify_certs,
            )
            result = import_daily_snapshot_file(es_writer, temp_path)
            return {"success": True, "result": result}
        finally:
            os.unlink(temp_path)
    except Exception as e:
        logger.exception("Failed to import CSV")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import CSV: {str(e)}",
        )
