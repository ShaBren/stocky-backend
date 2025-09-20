"""
Backup and restore endpoints for database management
"""
import gzip
import base64
import binascii
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from ...core.security import require_admin
from ...db.database import get_db, engine
from ...core.config import settings
from ...schemas.schemas import (
    BackupResponse, 
    BackupImportRequest, 
    BackupImportResponse
)
from ...models.models import User

router = APIRouter()


def get_database_file_path() -> str:
    """Extract database file path from DATABASE_URL"""
    if "sqlite:///" in settings.DATABASE_URL:
        return settings.DATABASE_URL.replace("sqlite:///", "")
    else:
        raise HTTPException(
            status_code=500, 
            detail="Backup functionality currently only supports SQLite databases"
        )


def get_table_names(db: Session) -> List[str]:
    """Get list of all table names in the database"""
    inspector = inspect(engine)
    return inspector.get_table_names()


@router.post("/create/full", response_model=BackupResponse)
async def create_full_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a full database backup as gzipped SQL dump.
    Admin access required.
    """
    try:
        db_path = get_database_file_path()
        
        # Get table information
        table_names = get_table_names(db)
        
        # Create SQL dump using sqlite3
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.sql', delete=False) as temp_file:
            result = subprocess.run([
                'sqlite3', db_path, '.dump'
            ], capture_output=True, text=True, check=True)
            
            temp_file.write(result.stdout)
            temp_file.flush()
            
            # Compress the SQL dump
            with open(temp_file.name, 'rb') as sql_file:
                sql_data = sql_file.read()
                compressed_data = gzip.compress(sql_data)
                
            # Clean up temp file
            Path(temp_file.name).unlink()
            
        return BackupResponse(
            backup_size=len(compressed_data),
            timestamp=datetime.now(),
            tables_included=table_names,
            message=f"Full backup created successfully. Size: {len(compressed_data)} bytes (compressed)"
        )
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create database backup: {e.stderr}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup creation failed: {str(e)}"
        )


@router.post("/create/full/download")
async def download_full_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create and download a full database backup as gzipped SQL file.
    Admin access required.
    """
    try:
        db_path = get_database_file_path()
        
        # Create SQL dump using sqlite3
        result = subprocess.run([
            'sqlite3', db_path, '.dump'
        ], capture_output=True, text=True, check=True)
        
        # Compress the SQL dump
        compressed_data = gzip.compress(result.stdout.encode('utf-8'))
        
        # Create response with appropriate headers
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stocky_backup_{timestamp}.sql.gz"
        
        def generate():
            yield compressed_data
            
        return StreamingResponse(
            generate(),
            media_type="application/gzip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create database backup: {e.stderr}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup creation failed: {str(e)}"
        )


@router.post("/import/partial", response_model=BackupImportResponse)
async def import_partial_backup(
    request: BackupImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Import a partial backup by applying SQL statements to existing database.
    This will add/update data without removing existing records.
    Admin access required.
    """
    try:
        # Decode and decompress the backup data
        compressed_data = base64.b64decode(request.backup_data)
        sql_data = gzip.decompress(compressed_data).decode('utf-8')
        
        # Execute SQL statements with transaction
        records_affected = 0
        tables_affected = set()
        
        # Split SQL into individual statements and execute
        statements = [stmt.strip() for stmt in sql_data.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement.upper().startswith(('INSERT', 'UPDATE', 'CREATE TABLE', 'CREATE INDEX')):
                try:
                    result = db.execute(text(statement))
                    records_affected += result.rowcount if result.rowcount else 0
                    
                    # Extract table name for tracking
                    if 'INSERT INTO' in statement.upper():
                        table_name = statement.split('INSERT INTO')[1].split()[0].strip('`"')
                        tables_affected.add(table_name)
                    elif 'UPDATE' in statement.upper():
                        table_name = statement.split('UPDATE')[1].split()[0].strip('`"')
                        tables_affected.add(table_name)
                        
                except Exception as e:
                    if not request.force:
                        db.rollback()
                        raise HTTPException(
                            status_code=400,
                            detail=f"SQL execution failed: {str(e)}. Use force=true to continue on errors."
                        )
                    # Continue on error if force=true
                    continue
        
        db.commit()
        
        return BackupImportResponse(
            success=True,
            message="Partial backup imported successfully",
            tables_affected=list(tables_affected),
            records_imported=records_affected,
            timestamp=datetime.now()
        )
        
    except binascii.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid base64 encoded backup data"
        )
    except gzip.BadGzipFile:
        raise HTTPException(
            status_code=400,
            detail="Invalid gzip compressed backup data"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Backup import failed: {str(e)}"
        )


@router.post("/import/full", response_model=BackupImportResponse)
async def import_full_backup(
    request: BackupImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Import a full backup by completely replacing the current database.
    WARNING: This will delete all existing data!
    Admin access required.
    """
    if not request.force:
        raise HTTPException(
            status_code=400,
            detail="Full database restore requires force=true to acknowledge data loss risk"
        )
        
    try:
            
        # Decode and decompress the backup data
        compressed_data = base64.b64decode(request.backup_data)
        sql_data = gzip.decompress(compressed_data).decode('utf-8')
        
        # Get current database info
        db_path = get_database_file_path()
        
        # Close current connection
        db.close()
        
        # Create backup of current database
        backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        subprocess.run(['cp', db_path, backup_path], check=True)
        
        try:
            # Write SQL to temporary file and restore
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(sql_data)
                temp_file.flush()
                
                # Replace database with restored data
                subprocess.run([
                    'sqlite3', db_path, f'.read {temp_file.name}'
                ], check=True, input='', text=True)
                
                # Clean up temp file
                Path(temp_file.name).unlink()
                
            # Reconnect to verify restore
            from ...db.database import SessionLocal
            new_db = SessionLocal()
            try:
                new_tables = get_table_names(new_db)
                
                return BackupImportResponse(
                    success=True,
                    message=f"Full database restore completed. Backup of original saved to: {backup_path}",
                    tables_affected=new_tables,
                    records_imported=-1,  # Unknown for full restore
                    timestamp=datetime.now()
                )
            finally:
                new_db.close()
                
        except Exception as restore_error:
            # Restore original database from backup
            subprocess.run(['cp', backup_path, db_path], check=True)
            raise HTTPException(
                status_code=500,
                detail=f"Restore failed, original database restored: {str(restore_error)}"
            )
            
    except binascii.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid base64 encoded backup data"
        )
    except gzip.BadGzipFile:
        raise HTTPException(
            status_code=400,
            detail="Invalid gzip compressed backup data"
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database operation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Full restore failed: {str(e)}"
        )


@router.post("/upload/import/partial", response_model=BackupImportResponse)
async def upload_partial_backup(
    file: UploadFile = File(...),
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Upload and import a partial backup from a gzipped SQL file.
    Admin access required.
    """
    if not file.filename.endswith('.sql.gz'):
        raise HTTPException(
            status_code=400,
            detail="File must be a gzipped SQL file (.sql.gz)"
        )
    
    try:
        # Read uploaded file
        file_content = await file.read()
        
        # Encode to base64 for processing
        base64_data = base64.b64encode(file_content).decode('utf-8')
        
        # Create request object and process
        import_request = BackupImportRequest(
            backup_data=base64_data,
            force=force
        )
        
        return await import_partial_backup(import_request, db, current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload and import failed: {str(e)}"
        )


@router.post("/upload/import/full", response_model=BackupImportResponse)
async def upload_full_backup(
    file: UploadFile = File(...),
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Upload and import a full backup from a gzipped SQL file.
    WARNING: This will replace the entire database!
    Admin access required.
    """
    if not file.filename.endswith('.sql.gz'):
        raise HTTPException(
            status_code=400,
            detail="File must be a gzipped SQL file (.sql.gz)"
        )
    
    try:
        # Read uploaded file
        file_content = await file.read()
        
        # Encode to base64 for processing
        base64_data = base64.b64encode(file_content).decode('utf-8')
        
        # Create request object and process
        import_request = BackupImportRequest(
            backup_data=base64_data,
            force=force
        )
        
        return await import_full_backup(import_request, db, current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload and import failed: {str(e)}"
        )