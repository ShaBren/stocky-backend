"""
Backup and restore endpoints — database-agnostic JSON export/import.
"""

import gzip
import json
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from ...core.security import require_admin
from ...db.database import engine, get_db
from ...models.models import User
from ...schemas.schemas import (
    BackupImportResponse,
    BackupStatusResponse,
)

router = APIRouter()

# Tables to skip during backup (SQLite internal, Alembic)
SKIP_TABLES = {"alembic_version"}

# Order matters for foreign key constraints during restore
TABLE_ORDER = [
    "users",
    "items",
    "locations",
    "skus",
    "alerts",
    "log_entries",
    "shopping_lists",
    "shopping_list_items",
    "shopping_list_logs",
    "sessions",
]


def _get_all_rows(db: Session, table_name: str) -> list[dict]:
    """Get all rows from a table as a list of dicts."""
    result = db.execute(text(f"SELECT * FROM {table_name}"))  # noqa: S608  # table_name from SQLAlchemy inspector
    columns = list(result.keys())
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]


def _serialize_value(val) -> object:
    """Convert non-JSON-serializable values."""
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val


@router.get("/download")
async def download_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Download a full database backup as a gzipped JSON file. Database-agnostic."""
    inspector = inspect(engine)
    all_tables = [t for t in inspector.get_table_names() if t not in SKIP_TABLES]

    export_data: dict[str, list[dict]] = {}
    for table in all_tables:
        rows = _get_all_rows(db, table)
        export_data[table] = [{k: _serialize_value(v) for k, v in row.items()} for row in rows]

    backup = {
        "metadata": {
            "version": "1.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "tables": sorted(all_tables),
        },
        "data": export_data,
    }

    json_bytes = json.dumps(backup, default=str).encode("utf-8")
    compressed = gzip.compress(json_bytes)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stocky_backup_{timestamp}.json.gz"

    def generate():
        yield compressed

    return StreamingResponse(
        generate(),
        media_type="application/gzip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/restore", response_model=BackupImportResponse)
async def restore_backup(
    file: UploadFile = File(...),
    mode: str = Query("merge", description="merge (additive) or replace (destructive)"),
    confirm: bool = Query(False, description="Required for replace mode"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Restore from a .json.gz backup file.

    - mode=merge: INSERT rows, skip conflicts (safe, additive)
    - mode=replace: TRUNCATE all tables then INSERT (destructive, requires confirm=true)
    """
    if mode not in ("merge", "replace"):
        raise HTTPException(status_code=400, detail="Mode must be 'merge' or 'replace'")
    if mode == "replace" and not confirm:
        raise HTTPException(status_code=400, detail="Replace mode requires confirm=true")

    if not file.filename or not file.filename.endswith(".json.gz"):
        raise HTTPException(status_code=400, detail="File must be a .json.gz backup")

    try:
        content = await file.read()
        json_str = gzip.decompress(content).decode("utf-8")
        backup: dict = json.loads(json_str)
    except (gzip.BadGzipFile, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid backup file: {e}")

    data = backup.get("data", {})
    if not data:
        raise HTTPException(status_code=400, detail="Backup contains no table data")

    if mode == "replace":
        # Delete all data in reverse dependency order.
        for table in reversed(TABLE_ORDER):
            if table in data:
                db.execute(text(f"DELETE FROM {table}"))  # noqa: S608  # table from trusted TABLE_ORDER
        db.commit()

    records_imported = 0
    tables_affected: list[str] = []

    for table in TABLE_ORDER:
        rows = data.get(table, [])
        if not rows:
            continue
        tables_affected.append(table)

        for row in rows:
            columns = ", ".join(row.keys())
            placeholders = ", ".join(f":{k}" for k in row)
            try:
                db.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"), row)  # noqa: S608  # table from trusted TABLE_ORDER
                records_imported += 1
            except Exception:
                if mode == "merge":
                    # Skip conflicting rows in merge mode
                    db.rollback()
                    continue
                raise

    db.commit()

    return BackupImportResponse(
        success=True,
        message=f"Restore complete ({mode} mode)",
        tables_affected=tables_affected,
        records_imported=records_imported,
        timestamp=datetime.now(),
    )


@router.get("/status", response_model=BackupStatusResponse)
async def backup_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get database status — table names and row counts."""
    inspector = inspect(engine)
    tables: dict[str, int] = {}
    for table_name in inspector.get_table_names():
        if table_name in SKIP_TABLES:
            continue
        result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))  # noqa: S608  # table_name from SQLAlchemy inspector
        tables[table_name] = result.scalar() or 0

    from ...core.config import settings

    return BackupStatusResponse(
        tables=tables,
        database_url=settings.DATABASE_URL.split("?")[0],  # strip query params for display
        timestamp=datetime.now(),
    )
