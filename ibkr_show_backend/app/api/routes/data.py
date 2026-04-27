import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import get_es_client
from app.clients.es_client import ESClientError
from app.core.config import get_settings

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
            from worker.core.config import get_settings
            from worker.clients.es_client import ElasticsearchWriter
            from worker.jobs.import_daily_snapshot import import_daily_snapshot_file

            settings = get_settings()
            es_writer = ElasticsearchWriter(settings)
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


@router.post("/clear")
async def clear_data() -> dict:
    try:
        settings = get_settings()
        es_client = get_es_client()

        all_indexes = [
            (settings.es_account_index, "accounts"),
            (settings.es_position_index, "positions"),
            (settings.es_trade_index, "trades"),
            (settings.es_cash_flow_index, "cash_flows"),
            (settings.es_price_history_index, "price_history"),
        ]

        results = {}
        for index_name, label in all_indexes:
            try:
                resp = es_client.delete_by_query(index=index_name, body={"query": {"match_all": {}}})
                results[label] = resp.get("deleted", 0)
            except ESClientError as exc:
                results[label] = f"error: {exc}"

        return {"success": True, "deleted": results}
    except Exception as e:
        logger.exception("Failed to clear data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear data: {str(e)}",
        )
