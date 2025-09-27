# Stocky Backend Source Code File Structure

This document provides a comprehensive overview of every source file in the Stocky Backend application, organized by directory and functionality.

**Last Updated:** September 27, 2025  
**Total Files:** 19

---

## Table of Contents

1. [Root Application Files](#root-application-files)
2. [API Layer](#api-layer)
3. [Core Components](#core-components)
4. [Database Layer](#database-layer)
5. [Data Models](#data-models)
6. [API Schemas](#api-schemas)
7. [CRUD Operations](#crud-operations)

---

## Root Application Files

### `src/stocky_backend/main.py`
**Purpose:** Main FastAPI application entry point and configuration  
**Key Responsibilities:**
- FastAPI application factory (`create_app()`)
- CORS middleware configuration using environment settings
- Application lifespan management (database table creation on startup)
- Router inclusion and URL path prefix setup (`/api/v1`)
- Development server configuration with uvicorn
- Application health and startup/shutdown lifecycle management

**Key Components:**
- `create_app()`: Creates and configures the FastAPI application instance
- `lifespan()`: Async context manager for application startup/shutdown
- CORS configuration with dynamic origins from settings
- Development server entry point for direct execution

---

## API Layer

### `src/stocky_backend/api/routes.py`
**Purpose:** Central API router that aggregates all endpoint modules  
**Key Responsibilities:**
- Creates the main `api_router` instance
- Includes all endpoint routers with appropriate prefixes and tags
- Provides the health check endpoint (`/health`)
- Centralizes API structure and organization

**Included Routers:**
- `/auth` - Authentication endpoints
- `/users` - User management endpoints  
- `/items` - Item/product management endpoints
- `/locations` - Storage location management endpoints
- `/skus` - Inventory/SKU management endpoints
- `/scanner` - Barcode scanner operations
- `/logs` - System logging endpoints
- `/alerts` - Alert management endpoints
- `/shopping-lists` - Shopping list management endpoints
- `/backup` - Database backup/restore endpoints

---

## API Endpoints

### `src/stocky_backend/api/endpoints/auth.py`
**Purpose:** Authentication and authorization endpoints  
**Key Responsibilities:**
- User login with username/password (form-data and JSON)
- JWT token generation and refresh
- User logout functionality
- Current user information retrieval
- API key generation and revocation
- Session management

**Endpoints:**
- `POST /refresh` - Refresh JWT access token
- `POST /login` - Login with form data
- `POST /login-json` - Login with JSON payload
- `POST /logout` - User logout
- `GET /me` - Get current user information
- `POST /generate-api-key` - Generate new API key
- `DELETE /revoke-api-key` - Revoke user's API key

---

### `src/stocky_backend/api/endpoints/users.py`
**Purpose:** User management operations (admin-only)  
**Key Responsibilities:**
- User CRUD operations (Create, Read, Update, Delete)
- User listing with pagination
- User role management
- Admin-only access control enforcement
- User account activation/deactivation

**Endpoints:**
- `GET /` - List all users (paginated)
- `POST /` - Create new user
- `GET /{user_id}` - Get specific user details
- `PUT /{user_id}` - Update user information
- `DELETE /{user_id}` - Delete user (soft delete)

---

### `src/stocky_backend/api/endpoints/items.py`
**Purpose:** Product/item catalog management  
**Key Responsibilities:**
- Item CRUD operations
- Product search functionality
- UPC code management and lookups
- Default storage type configuration
- Item catalog organization

**Endpoints:**
- `GET /` - List all items (paginated)
- `POST /` - Create new item
- `GET /search` - Search items by name/UPC
- `GET /{item_id}` - Get specific item details
- `PUT /{item_id}` - Update item information
- `DELETE /{item_id}` - Delete item (soft delete)
- `GET /upc/{upc}` - Find item by UPC code

---

### `src/stocky_backend/api/endpoints/locations.py`
**Purpose:** Storage location management  
**Key Responsibilities:**
- Location CRUD operations
- Storage type categorization (Pantry, Refrigerator, Freezer, Counter)
- Location search functionality
- Storage organization and hierarchy

**Endpoints:**
- `GET /` - List all locations (paginated)
- `POST /` - Create new location
- `GET /search` - Search locations by name
- `GET /{location_id}` - Get specific location details
- `PUT /{location_id}` - Update location information
- `DELETE /{location_id}` - Delete location (soft delete)
- `GET /name/{name}` - Find location by exact name

---

### `src/stocky_backend/api/endpoints/skus.py`
**Purpose:** Inventory/SKU (Stock Keeping Unit) management  
**Key Responsibilities:**
- Inventory CRUD operations
- Quantity tracking and updates
- Expiry date management
- Low stock detection and alerts
- Item-location relationship management

**Endpoints:**
- `GET /` - List all SKUs (paginated)
- `POST /` - Create new SKU (add inventory)
- `GET /search` - Search SKUs by item name/notes
- `GET /{sku_id}` - Get specific SKU details
- `PUT /{sku_id}` - Update SKU information
- `PUT /{sku_id}/quantity` - Quick quantity update
- `DELETE /{sku_id}` - Delete SKU (soft delete)
- `GET /low-stock` - Get items with low stock levels

---

### `src/stocky_backend/api/endpoints/scanner.py`
**Purpose:** Barcode scanner operations and device management  
**Key Responsibilities:**
- Barcode scanning and processing
- Scanner device association with users
- UPC code lookups and external service integration
- Scan result processing and suggested actions
- Scanner status monitoring

**Endpoints:**
- `POST /scan` - Process barcode scan
- `GET /status/{scanner_id}` - Get scanner device status
- `POST /associate` - Associate scanner with user
- `DELETE /associate/{scanner_id}` - Disassociate scanner
- `GET /associations` - List all scanner associations
- `POST /lookup/{upc}` - External UPC lookup service

---

### `src/stocky_backend/api/endpoints/logs.py`
**Purpose:** System logging and audit trails  
**Key Responsibilities:**
- System log retrieval and filtering
- Audit trail management
- Log level filtering (DEBUG, INFO, WARNING, ERROR)
- Module-based log filtering
- Administrative logging access

**Endpoints:**
- `GET /` - Retrieve system logs with filtering options

---

### `src/stocky_backend/api/endpoints/alerts.py`
**Purpose:** Alert and notification management  
**Key Responsibilities:**
- Alert creation and management
- Low stock alerts
- System notification handling
- Alert acknowledgment tracking
- Alert lifecycle management

**Endpoints:**
- `GET /` - List alerts with filtering
- `POST /` - Create new alert

---

### `src/stocky_backend/api/endpoints/shopping_lists.py`
**Purpose:** Shopping list management and collaborative editing  
**Key Responsibilities:**
- Shopping list CRUD operations (create, read, update, delete)
- Public/private visibility management and access control
- Shopping list item management (add, update, remove items)
- Complete audit logging of all list and item changes
- List duplication functionality
- Collaborative editing (public lists editable by any user)

**Endpoints:**
- `GET /` - List accessible shopping lists (paginated)
- `GET /{list_id}` - Get shopping list details with items
- `POST /` - Create new shopping list
- `PUT /{list_id}` - Update shopping list metadata
- `DELETE /{list_id}` - Delete shopping list (soft delete)
- `POST /{list_id}/duplicate` - Duplicate shopping list with items
- `POST /{list_id}/items` - Add item to shopping list
- `PUT /{list_id}/items/{item_id}` - Update item quantity
- `DELETE /{list_id}/items/{item_id}` - Remove item from list
- `GET /{list_id}/logs` - Get shopping list change logs

---

### `src/stocky_backend/api/endpoints/backup.py`
**Purpose:** Database backup and restore operations (admin-only)  
**Key Responsibilities:**
- Full database backup creation
- Partial data backup/restore
- Database restoration from backup files
- Backup file upload and download
- Data integrity and safety checks

**Endpoints:**
- `POST /create/full` - Create full database backup
- `POST /create/full/download` - Create and download backup
- `POST /import/partial` - Import partial backup data
- `POST /import/full` - Restore full database from backup
- `POST /upload/import/partial` - Upload and import partial backup
- `POST /upload/import/full` - Upload and restore full backup

---

## Core Components

### `src/stocky_backend/core/config.py`
**Purpose:** Application configuration and environment variable management  
**Key Responsibilities:**
- Environment variable loading and validation using Pydantic Settings
- Default configuration values for all application settings
- CORS origins parsing and validation
- Database URL configuration
- Security settings (JWT, API keys, timeouts)
- Application runtime configuration (debug mode, logging, etc.)

**Key Settings:**
- `SECRET_KEY` - JWT signing key (with security validation)
- `ALLOWED_ORIGINS` - CORS allowed origins (with parsing logic)
- `DATABASE_URL` - Database connection string
- `DEBUG` - Development/production mode flag
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiration
- External service configuration (UDA service settings)

---

### `src/stocky_backend/core/auth.py`
**Purpose:** Authentication utilities and JWT token management  
**Key Responsibilities:**
- Password hashing and verification using bcrypt
- JWT token creation, signing, and verification
- Token payload encoding/decoding
- API key generation with secure random strings
- User authentication workflows
- Token expiration and refresh logic

**Key Functions:**
- `hash_password()` - Secure password hashing
- `verify_password()` - Password verification against hash
- `create_access_token()` - JWT token generation
- `verify_token_payload()` - JWT token validation and parsing
- `create_token_response()` - Complete token response with refresh tokens
- `generate_api_key()` - Secure API key generation

---

### `src/stocky_backend/core/security.py`
**Purpose:** FastAPI security dependencies and authorization  
**Key Responsibilities:**
- JWT bearer token authentication dependency
- API key authentication dependency
- Role-based access control enforcement
- User authorization middleware
- Security scheme definitions for FastAPI
- Permission checking and user context management

**Key Dependencies:**
- `get_current_user_from_token()` - Extract user from JWT
- `get_current_user_from_api_key()` - Extract user from API key
- `get_current_active_user()` - Get authenticated active user
- `require_admin()` - Enforce admin role requirement
- `require_user_role()` - Flexible role requirement enforcement

---

## Database Layer

### `src/stocky_backend/db/database.py`
**Purpose:** Database connection and session management  
**Key Responsibilities:**
- SQLAlchemy engine configuration
- Database session factory setup
- Connection string processing and driver selection
- Database session dependency injection for FastAPI
- SQLAlchemy Base class for model inheritance

**Key Components:**
- `engine` - SQLAlchemy database engine instance
- `SessionLocal` - Session factory for database connections
- `Base` - Declarative base class for all models
- `get_db()` - FastAPI dependency for database sessions
- Database URL normalization for SQLite compatibility

---

## Data Models

### `src/stocky_backend/models/models.py`
**Purpose:** SQLAlchemy ORM models for all database tables  
**Key Responsibilities:**
- Database table definitions using SQLAlchemy ORM
- Relationship definitions between entities
- Data validation constraints and database indexes
- Enum definitions for controlled vocabularies
- Automatic timestamp management (created_at, updated_at)

**Models Defined:**
- `User` - User accounts with roles and authentication
- `Item` - Product catalog entries
- `Location` - Storage locations with types
- `SKU` - Inventory items (item-location pairs)
- `Alert` - System alerts and notifications
- `LogEntry` - System audit logs

**Enums:**
- `UserRole` - User permission levels (ADMIN, MEMBER)
- `StorageType` - Location categories (PANTRY, REFRIGERATOR, FREEZER, COUNTER)

---

## API Schemas

### `src/stocky_backend/schemas/schemas.py`
**Purpose:** Pydantic models for API request/response validation  
**Key Responsibilities:**
- Request body validation schemas
- Response serialization models
- Data type validation and conversion
- API input sanitization and constraint enforcement
- Automatic documentation generation for OpenAPI/Swagger

**Schema Categories:**
- **Authentication schemas:** `Token`, `LoginRequest`, `TokenData`
- **User schemas:** `UserCreate`, `UserUpdate`, `UserResponse`
- **Item schemas:** `ItemCreate`, `ItemUpdate`, `ItemResponse`
- **Location schemas:** `LocationCreate`, `LocationUpdate`, `LocationResponse`
- **SKU schemas:** `SKUCreate`, `SKUUpdate`, `SKUResponse`, `SKUQuantityUpdate`
- **Alert schemas:** `AlertCreate`, `AlertUpdate`, `AlertResponse`
- **Scanner schemas:** `ScanRequest`, `ScanResponse`, `ScannerStatus`, `ScannerAssociation`
- **Search schemas:** `SearchRequest`, `SearchResponse`
- **Backup schemas:** `BackupResponse`, `BackupImportRequest`, `BackupImportResponse`

---

## CRUD Operations

### `src/stocky_backend/crud/crud.py`
**Purpose:** Main CRUD (Create, Read, Update, Delete) operations  
**Key Responsibilities:**
- Database operations for all models
- Generic CRUD base class with common operations
- Specialized operations for each entity type
- Search and filtering functionality
- Relationship management between entities
- Data integrity and constraint handling

**CRUD Classes:**
- `UserCRUD` - User management operations
- `ItemCRUD` - Item catalog operations
- `LocationCRUD` - Location management operations
- `SKUCRUD` - Inventory management operations
- `AlertCRUD` - Alert management operations
- `LogEntryCRUD` - System logging operations

---

## File Interdependencies

### Import Flow
```
main.py
├── core/config.py (settings)
├── core/security.py (authentication)
├── api/routes.py (API routing)
│   └── api/endpoints/*.py (individual endpoints)
│       ├── core/auth.py (JWT/password handling)
│       ├── core/security.py (authorization)
│       ├── db/database.py (database sessions)
│       ├── models/models.py (database models)
│       ├── schemas/schemas.py (request/response validation)
│       └── crud/crud.py (database operations)
```

### Key Architectural Patterns

1. **Layered Architecture:**
   - API Layer (endpoints) → Business Logic (CRUD) → Data Layer (models)

2. **Dependency Injection:**
   - Database sessions injected via `get_db()`
   - Authentication via security dependencies

3. **Configuration Management:**
   - Centralized settings in `core/config.py`
   - Environment variable integration

4. **Security First:**
   - Authentication at core level
   - Role-based authorization
   - Input validation through schemas

---

## Development Notes

### Active Files (Production)
- All source files are actively used in production

### File Naming Conventions
- **Endpoints:** Named by resource type (e.g., `users.py`, `items.py`)
- **Core:** Named by functionality (e.g., `auth.py`, `security.py`)
- **Schemas:** Grouped by purpose (`schemas.py` contains all Pydantic models)
- **Models:** Single file (`models.py`) with all SQLAlchemy models

### Code Organization Principles
- **Single Responsibility:** Each file has a clear, focused purpose
- **Separation of Concerns:** API, business logic, and data layers are separated
- **Reusability:** Common functionality is centralized in core modules
- **Testability:** Clear dependencies and injection patterns for testing

---

*This documentation reflects the current state of the Stocky Backend codebase as of September 21, 2025.*