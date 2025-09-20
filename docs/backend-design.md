Stocky Backend - Application & Environment Design
Version: 1.2 (Final)
Date: August 5, 2025

1. Project & Directory Structure
The project will be organized as a standard, installable Python package.

stocky-backend/
│
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── pyproject.toml
├── README.md
│
└── src/
    └── stocky-backend/
        │
        ├── __init__.py
        ├── api/
        ├── core/
        ├── crud/
        ├── db/
        │   ├── alembic/
        │   └── initial\_data.py  # Script to create default admin
        │   └── demo\_data.py  # Script to insert sample data for demo/testing
        ├── models/
        ├── schemas/
        ├── services/
        └── main.py

2. Dependency Management & Licensing
Dependencies will be managed via uv and a requirements.txt file. The project and all its core dependencies will use the MIT License.

3. Configuration Management
Configuration will be managed via environment variables, with SQLite as the default database. PostgreSQL is supported as an optional, user-configured alternative.

4. Application Logging
The /log API endpoint will be served from an in-memory, capped collection (e.g., a collections.deque with a maxlen of 10,000). A custom logging handler will be implemented to push log records into this in-memory store.

5. Dockerization & Deployment
The application is designed to be run as a Docker container. The default docker-compose.yml will be configured for a simple, single-service setup using SQLite, making the initial startup process trivial.

6. Testing Strategy
A multi-layered testing strategy using pytest will be implemented, covering unit, integration, and API tests. Integration tests will run against a temporary, clean test database.

7. Database Migrations
Database schema changes will be managed using Alembic, allowing for version-controlled, incremental updates.

8. Initial Data Seeding
A manual script, src/stocky/db/initial_data.py, will be provided. Its sole purpose is to create the initial Admin user, allowing the administrator to then set up the rest of the system (locations, scanners, etc.) through the UI. An optional, separate script for generating comprehensive demo data can be created for testing and demonstration purposes.

9. Backup and Restore System
For deployment safety and data management, the system includes comprehensive backup and restore functionality through admin-only API endpoints.

## Backup Endpoints (Admin Only)

All backup endpoints require admin authentication and are accessible under `/api/v1/backup/`:

### Full Database Backup
- **POST /backup/create/full** - Creates a full database backup and returns metadata
- **POST /backup/create/full/download** - Creates and downloads a gzipped SQL backup file

### Database Import/Restore
- **POST /backup/import/partial** - Imports SQL data into existing database (additive)
- **POST /backup/import/full** - Completely replaces database (destructive, requires force=true)

### File Upload Variants
- **POST /backup/upload/import/partial** - Upload gzipped SQL file for partial import
- **POST /backup/upload/import/full** - Upload gzipped SQL file for full restore

## Security Considerations

- **Admin-only access**: All backup operations require admin role authentication
- **Force confirmation**: Full database restore requires explicit force=true flag
- **Automatic backups**: Full restore creates timestamped backup of original database
- **SQLite-specific**: Current implementation supports SQLite databases only
- **Error handling**: Comprehensive validation for file formats and data integrity

## Data Formats

**Backup Response:**
```json
{
  "backup_size": 12345,
  "timestamp": "2025-09-20T10:30:00Z", 
  "tables_included": ["users", "items", "locations"],
  "message": "Full backup created successfully..."
}
```

**Import Request:**
```json
{
  "backup_data": "base64-encoded-gzipped-sql-data",
  "force": false
}
```

**Import Response:**
```json
{
  "success": true,
  "message": "Import completed successfully",
  "tables_affected": ["users", "items"],
  "records_imported": 150,
  "timestamp": "2025-09-20T10:35:00Z"
}
```

## Usage Examples

**Create and download backup:**
```bash
curl -X POST "http://localhost:8000/api/v1/backup/create/full/download" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -o backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Restore from backup (with safety confirmation):**
```bash
curl -X POST "http://localhost:8000/api/v1/backup/import/full" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_data": "BASE64_ENCODED_GZIP_DATA",
    "force": true
  }'
```

## Deployment Integration

This backup system is designed for:
- **Pre-deployment backups**: Ensure data safety before updates
- **Database migrations**: Export/import data across environments  
- **Disaster recovery**: Quick restoration from known good states
- **Environment synchronization**: Copy production data to staging

9. Backup and Restore API
The system provides comprehensive backup and restore functionality for deployment scenarios.

### Security Requirements
- All backup endpoints require Admin-level authentication
- JWT tokens must be valid and user must have `UserRole.ADMIN`
- No backup operations are available to regular users

### Backup Endpoints

#### POST /api/v1/backup/create/full
Creates a complete database backup as compressed SQL.

**Request Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Response:**
```json
{
  "backup_size": 1024,
  "timestamp": "2025-09-20T10:30:00Z",
  "tables_included": ["users", "items", "locations", "skus", "logs"],
  "message": "Full backup created successfully. Size: 1024 bytes (compressed)"
}
```

#### POST /api/v1/backup/create/full/download
Creates and downloads a complete database backup file.

**Request Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Response:**
- Content-Type: `application/gzip`
- Content-Disposition: `attachment; filename=stocky_backup_20250920_103000.sql.gz`
- Body: Gzipped SQL dump file

#### POST /api/v1/backup/import/partial
Imports backup data into existing database (additive operation).

**Request Headers:**
```
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "backup_data": "<base64_encoded_gzipped_sql>",
  "force": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Partial backup imported successfully",
  "tables_affected": ["users", "items"],
  "records_imported": 42,
  "timestamp": "2025-09-20T10:35:00Z"
}
```

#### POST /api/v1/backup/import/full
Replaces entire database with backup data (destructive operation).

**Request Headers:**
```
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "backup_data": "<base64_encoded_gzipped_sql>",
  "force": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Full database restore completed. Backup of original saved to: /path/to/backup.db",
  "tables_affected": ["users", "items", "locations", "skus", "logs"],
  "records_imported": -1,
  "timestamp": "2025-09-20T10:40:00Z"
}
```

#### POST /api/v1/backup/upload/import/partial
Upload and import partial backup from file.

**Request Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Form Data:**
- `file`: Gzipped SQL file (.sql.gz)
- `force`: boolean (optional, default: false)

#### POST /api/v1/backup/upload/import/full
Upload and import full backup from file.

**Request Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Form Data:**
- `file`: Gzipped SQL file (.sql.gz)
- `force`: boolean (required: true for safety)

### Implementation Details

**Database Support:**
- Currently supports SQLite databases only
- Uses `sqlite3` command-line tool for reliable SQL dumps
- Future PostgreSQL support planned

**Error Handling:**
- Invalid base64 data: HTTP 400
- Invalid gzip data: HTTP 400
- Insufficient permissions: HTTP 403
- SQL execution errors: HTTP 400/500
- File format validation for uploads

**Safety Features:**
- Full restore requires `force=true` to acknowledge data loss risk
- Original database backed up before full restore
- Automatic rollback on restore failure
- Transaction isolation for partial imports

**File Format:**
- Backup data encoded as base64-encoded gzipped SQL
- Compatible with standard SQL dump formats
- Upload endpoints accept .sql.gz files directly

### Usage Examples

**Creating a backup:**
```bash
curl -X POST "http://localhost:8000/api/v1/backup/create/full" \
  -H "Authorization: Bearer <admin_token>"
```

**Downloading a backup:**
```bash
curl -X POST "http://localhost:8000/api/v1/backup/create/full/download" \
  -H "Authorization: Bearer <admin_token>" \
  -o stocky_backup.sql.gz
```

**Uploading a backup file:**
```bash
curl -X POST "http://localhost:8000/api/v1/backup/upload/import/partial" \
  -H "Authorization: Bearer <admin_token>" \
  -F "file=@backup.sql.gz" \
  -F "force=true"
```
