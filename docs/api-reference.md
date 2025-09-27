# Stocky Backend API Reference

**Version:** v1  
**Base URL:** `https://your-domain.com/api/v1`  
**Authentication:** JWT Bearer Token or API Key  

## Table of Contents

1. [Authentication](#authentication)
2. [Authentication Endpoints](#authentication-endpoints)
3. [User Management](#user-management)
4. [Item Management](#item-management)
5. [Location Management](#location-management)
6. [SKU/Inventory Management](#sku-inventory-management)
7. [Scanner Operations](#scanner-operations)
8. [Logging](#logging)
8. [Alerts](#alerts)
9. [Shopping Lists](#shopping-lists)
10. [Backup & Restore](#backup--restore)
11. [Health Check](#health-check)
12. [Error Codes](#error-codes)
13. [Environment Configuration](#environment-configuration)

---

## Authentication

The Stocky Backend API supports two authentication methods:

### JWT Bearer Token Authentication
```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication
```http
X-API-Key: <api_key>
```

### User Roles
- **ADMIN**: Full access to all endpoints including user management
- **MEMBER**: Access to inventory operations, limited administrative functions

---

## Authentication Endpoints

All authentication endpoints are under `/auth/`

### POST /auth/login
**Description:** Login with username/password (form data)  
**Authentication:** None required  
**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**
```
username=your_username&password=your_password
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": 1,
  "role": "ADMIN",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials or inactive user

---

### POST /auth/login-json
**Description:** Login with username/password (JSON payload)  
**Authentication:** None required  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:** Same as `/auth/login`

**Validation:**
- `username`: 3-50 characters
- `password`: minimum 8 characters

---

### POST /auth/refresh
**Description:** Refresh access token using valid JWT  
**Authentication:** Bearer Token required

**Response:** `200 OK`
```json
{
  "access_token": "new_jwt_token_here",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": 1,
  "role": "ADMIN",
  "refresh_token": "new_refresh_token_here"
}
```

---

### POST /auth/logout
**Description:** Logout current user (client should discard tokens)  
**Authentication:** Bearer Token required

**Response:** `200 OK`
```json
{
  "message": "User username logged out successfully"
}
```

---

### GET /auth/me
**Description:** Get current user information  
**Authentication:** Bearer Token required

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "ADMIN",
  "is_active": true,
  "created_at": "2025-09-20T10:00:00Z",
  "updated_at": "2025-09-20T10:00:00Z"
}
```

---

### POST /auth/generate-api-key
**Description:** Generate new API key for current user  
**Authentication:** Bearer Token required

**Response:** `200 OK`
```json
{
  "message": "API key generated successfully",
  "api_key": "sk-1234567890abcdef",
  "note": "Store this API key securely. It will not be shown again."
}
```

---

### DELETE /auth/revoke-api-key
**Description:** Revoke current user's API key  
**Authentication:** Bearer Token required

**Response:** `200 OK`
```json
{
  "message": "API key revoked successfully"
}
```

---

## User Management

All user management endpoints are under `/users/` and require **ADMIN** role.

### GET /users/
**Description:** List all users  
**Authentication:** ADMIN required

**Query Parameters:**
- `skip` (int, default: 0): Number of users to skip
- `limit` (int, default: 100, max: 1000): Number of users to return

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2025-09-20T10:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z"
  }
]
```

---

### POST /users/
**Description:** Create new user  
**Authentication:** ADMIN required

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password",
  "role": "MEMBER"
}
```

**Validation:**
- `username`: 3-50 characters, unique
- `email`: valid email format, unique
- `password`: minimum 8 characters
- `role`: "ADMIN" or "MEMBER" (default: "MEMBER")

**Response:** `201 Created`
```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@example.com",
  "role": "MEMBER",
  "is_active": true,
  "created_at": "2025-09-20T10:00:00Z",
  "updated_at": "2025-09-20T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Username/email already exists or validation errors

---

### GET /users/{user_id}
**Description:** Get specific user by ID  
**Authentication:** ADMIN required

**Path Parameters:**
- `user_id` (int): User ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "ADMIN",
  "is_active": true,
  "created_at": "2025-09-20T10:00:00Z",
  "updated_at": "2025-09-20T10:00:00Z"
}
```

**Error Responses:**
- `404 Not Found`: User not found

---

### PUT /users/{user_id}
**Description:** Update user  
**Authentication:** ADMIN required

**Path Parameters:**
- `user_id` (int): User ID

**Request Body:**
```json
{
  "username": "updated_username",
  "email": "updated@example.com",
  "role": "ADMIN",
  "is_active": false
}
```

**Response:** `200 OK` (returns updated user)

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: Validation errors or username/email conflicts

---

### DELETE /users/{user_id}
**Description:** Delete user (soft delete)  
**Authentication:** ADMIN required

**Path Parameters:**
- `user_id` (int): User ID

**Response:** `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: Cannot delete yourself

---

## Item Management

All item endpoints are under `/items/`

### GET /items/
**Description:** List all items  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `skip` (int, default: 0): Number of items to skip
- `limit` (int, default: 100, max: 500): Number of items to return

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Apples",
    "description": "Red apples",
    "upc": "123456789012",
    "default_storage_type": "PANTRY",
    "is_active": true,
    "uda_fetched": false,
    "uda_fetch_attempted": false,
    "created_at": "2025-09-20T10:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z"
  }
]
```

---

### POST /items/
**Description:** Create new item  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "name": "Bananas",
  "description": "Yellow bananas",
  "upc": "123456789013",
  "default_storage_type": "PANTRY"
}
```

**Validation:**
- `name`: 1-200 characters, required
- `description`: max 1000 characters, optional
- `upc`: 8-20 characters, optional, unique if provided
- `default_storage_type`: "PANTRY", "REFRIGERATOR", "FREEZER", "COUNTER", optional

**Response:** `201 Created` (returns created item)

---

### GET /items/search
**Description:** Search items by name or UPC  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `q` (string): Search query
- `limit` (int, default: 20, max: 100): Number of results

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Apples",
    "description": "Red apples",
    "upc": "123456789012",
    "default_storage_type": "PANTRY",
    "is_active": true,
    "uda_fetched": false,
    "uda_fetch_attempted": false,
    "created_at": "2025-09-20T10:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z"
  }
]
```

---

### GET /items/{item_id}
**Description:** Get specific item by ID  
**Authentication:** Bearer Token or API Key required

**Response:** `200 OK` (returns item details)

**Error Responses:**
- `404 Not Found`: Item not found

---

### PUT /items/{item_id}
**Description:** Update item  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "name": "Updated Item Name",
  "description": "Updated description",
  "upc": "123456789014",
  "default_storage_type": "REFRIGERATOR",
  "is_active": true
}
```

**Response:** `200 OK` (returns updated item)

---

### DELETE /items/{item_id}
**Description:** Delete item (soft delete)  
**Authentication:** Bearer Token or API Key required

**Response:** `200 OK`
```json
{
  "message": "Item deleted successfully"
}
```

---

### GET /items/upc/{upc}
**Description:** Get item by UPC code  
**Authentication:** Bearer Token or API Key required

**Path Parameters:**
- `upc` (string): UPC code

**Response:** `200 OK` (returns item details)

**Error Responses:**
- `404 Not Found`: Item with UPC not found

---

## Location Management

All location endpoints are under `/locations/`

### GET /locations/
**Description:** List all locations  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `skip` (int, default: 0): Number of locations to skip
- `limit` (int, default: 100, max: 500): Number of locations to return

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Pantry",
    "description": "Main pantry storage",
    "storage_type": "PANTRY",
    "is_active": true,
    "created_at": "2025-09-20T10:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z"
  }
]
```

---

### POST /locations/
**Description:** Create new location  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "name": "Basement Freezer",
  "description": "Additional freezer storage",
  "storage_type": "FREEZER"
}
```

**Validation:**
- `name`: 1-100 characters, required
- `description`: max 1000 characters, optional
- `storage_type`: "PANTRY", "REFRIGERATOR", "FREEZER", "COUNTER", required

**Response:** `201 Created` (returns created location)

---

### GET /locations/search
**Description:** Search locations by name  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `q` (string): Search query
- `limit` (int, default: 20, max: 100): Number of results

---

### GET /locations/{location_id}
**Description:** Get specific location by ID  
**Authentication:** Bearer Token or API Key required

---

### PUT /locations/{location_id}
**Description:** Update location  
**Authentication:** Bearer Token or API Key required

---

### DELETE /locations/{location_id}
**Description:** Delete location (soft delete)  
**Authentication:** Bearer Token or API Key required

---

### GET /locations/name/{name}
**Description:** Get location by name  
**Authentication:** Bearer Token or API Key required

**Path Parameters:**
- `name` (string): Location name

---

## SKU/Inventory Management

All SKU endpoints are under `/skus/`

### GET /skus/
**Description:** List all SKUs (inventory items)  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `skip` (int, default: 0): Number of SKUs to skip
- `limit` (int, default: 100, max: 500): Number of SKUs to return

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "quantity": 5.0,
    "unit": "pieces",
    "expiry_date": "2025-12-31T00:00:00Z",
    "notes": "Organic apples",
    "is_active": true,
    "item_id": 1,
    "location_id": 1,
    "created_at": "2025-09-20T10:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z"
  }
]
```

---

### POST /skus/
**Description:** Create new SKU (add item to location)  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "item_id": 1,
  "location_id": 1,
  "quantity": 5.0,
  "unit": "pieces",
  "expiry_date": "2025-12-31T00:00:00Z",
  "notes": "Organic apples"
}
```

**Validation:**
- `item_id`: valid item ID, required
- `location_id`: valid location ID, required
- `quantity`: non-negative number, required
- `unit`: max 20 characters, optional
- `expiry_date`: ISO datetime, optional
- `notes`: max 1000 characters, optional

**Response:** `201 Created` (returns created SKU)

---

### GET /skus/search
**Description:** Search SKUs by item name or notes  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `q` (string): Search query
- `limit` (int, default: 20, max: 100): Number of results

---

### GET /skus/{sku_id}
**Description:** Get specific SKU by ID  
**Authentication:** Bearer Token or API Key required

---

### PUT /skus/{sku_id}
**Description:** Update SKU  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "quantity": 3.0,
  "unit": "pieces",
  "expiry_date": "2025-11-30T00:00:00Z",
  "notes": "Updated notes",
  "location_id": 2,
  "is_active": true
}
```

---

### PUT /skus/{sku_id}/quantity
**Description:** Update only SKU quantity (quick update)  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "quantity": 10
}
```

**Response:** `200 OK` (returns updated SKU)

---

### DELETE /skus/{sku_id}
**Description:** Delete SKU (soft delete)  
**Authentication:** Bearer Token or API Key required

**Response:** `200 OK`
```json
{
  "message": "SKU deleted successfully"
}
```

---

### GET /skus/low-stock
**Description:** Get items with low stock (quantity <= threshold)  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `skip` (int, default: 0): Number of SKUs to skip
- `limit` (int, default: 100, max: 500): Number of SKUs to return

**Response:** `200 OK` (returns array of low-stock SKUs)

---

## Scanner Operations

All scanner endpoints are under `/scanner/`

### POST /scanner/scan
**Description:** Process barcode scan  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "upc": "123456789012",
  "scanner_id": "scanner_001",
  "location_hint": "Pantry"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "item": {
    "id": 1,
    "name": "Apples",
    "description": "Red apples",
    "upc": "123456789012",
    "default_storage_type": "PANTRY",
    "is_active": true,
    "uda_fetched": false,
    "uda_fetch_attempted": false,
    "created_at": "2025-09-20T10:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z"
  },
  "skus": [
    {
      "id": 1,
      "quantity": 5.0,
      "unit": "pieces",
      "expiry_date": null,
      "notes": null,
      "is_active": true,
      "item_id": 1,
      "location_id": 1,
      "created_at": "2025-09-20T10:00:00Z",
      "updated_at": "2025-09-20T10:00:00Z"
    }
  ],
  "message": "Item found in inventory",
  "suggested_actions": ["Update quantity", "Check expiry date"]
}
```

---

### GET /scanner/status/{scanner_id}
**Description:** Get scanner status  
**Authentication:** Bearer Token or API Key required

**Response:** `200 OK`
```json
{
  "scanner_id": "scanner_001",
  "is_associated": true,
  "associated_user": "admin",
  "last_seen": "2025-09-20T10:00:00Z"
}
```

---

### POST /scanner/associate
**Description:** Associate scanner with user  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "scanner_id": "scanner_001",
  "user_id": "admin"
}
```

---

### DELETE /scanner/associate/{scanner_id}
**Description:** Disassociate scanner from user  
**Authentication:** Bearer Token or API Key required

---

### GET /scanner/associations
**Description:** Get all scanner associations  
**Authentication:** Bearer Token or API Key required

---

### POST /scanner/lookup/{upc}
**Description:** Lookup item by UPC (external service)  
**Authentication:** Bearer Token or API Key required

**Path Parameters:**
- `upc` (string): UPC code to lookup

---

## Logging

### GET /logs/
**Description:** Get system logs  
**Authentication:** ADMIN required

**Query Parameters:**
- `skip` (int, default: 0): Number of logs to skip
- `limit` (int, default: 100, max: 1000): Number of logs to return
- `level` (string): Filter by log level ("DEBUG", "INFO", "WARNING", "ERROR")
- `module` (string): Filter by module name

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "level": "INFO",
    "message": "User logged in",
    "module": "auth",
    "function": "login",
    "user_id": 1,
    "extra_data": {},
    "created_at": "2025-09-20T10:00:00Z"
  }
]
```

---

## Alerts

### GET /alerts/
**Description:** Get system alerts  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `skip` (int, default: 0): Number of alerts to skip
- `limit` (int, default: 100): Number of alerts to return
- `active_only` (bool, default: true): Show only active alerts

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "alert_type": "LOW_STOCK",
    "message": "Low stock alert for Apples",
    "threshold_value": 2.0,
    "is_active": true,
    "is_acknowledged": false,
    "acknowledged_at": null,
    "sku_id": 1,
    "created_at": "2025-09-20T10:00:00Z",
    "updated_at": "2025-09-20T10:00:00Z"
  }
]
```

---

### POST /alerts/
**Description:** Create new alert  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "alert_type": "LOW_STOCK",
  "message": "Custom alert message",
  "threshold_value": 1.0,
  "sku_id": 1
}
```

---

## Shopping Lists

All shopping list endpoints are under `/shopping-lists/`

### GET /shopping-lists/
**Description:** List shopping lists accessible to current user (public + own private)  
**Authentication:** Bearer Token or API Key required

**Query Parameters:**
- `skip` (int, default: 0): Number of lists to skip
- `limit` (int, default: 100): Number of lists to return (max: 1000)
- `include_deleted` (bool, default: false): Include deleted lists (admin only)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "name": "Weekly Groceries",
      "is_public": true,
      "creator": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "MEMBER",
        "is_active": true,
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2025-09-01T10:00:00Z"
      },
      "item_count": 5,
      "created_at": "2025-09-27T10:00:00Z",
      "updated_at": "2025-09-27T11:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

---

### GET /shopping-lists/{list_id}
**Description:** Get shopping list details with all items  
**Authentication:** Bearer Token or API Key required  
**Access:** Public lists or user's own private lists

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Weekly Groceries",
  "is_public": true,
  "creator": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "MEMBER",
    "is_active": true,
    "created_at": "2025-09-01T10:00:00Z",
    "updated_at": "2025-09-01T10:00:00Z"
  },
  "items": [
    {
      "id": 1,
      "item": {
        "id": 10,
        "name": "Whole Milk",
        "description": "1 gallon whole milk",
        "upc": "123456789012",
        "default_storage_type": "refrigerator",
        "is_active": true,
        "uda_fetched": false,
        "uda_fetch_attempted": false,
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2025-09-01T10:00:00Z"
      },
      "quantity": 2,
      "created_at": "2025-09-27T10:15:00Z",
      "updated_at": "2025-09-27T10:15:00Z"
    }
  ],
  "created_at": "2025-09-27T10:00:00Z",
  "updated_at": "2025-09-27T11:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Shopping list not found or access denied

---

### POST /shopping-lists/
**Description:** Create a new shopping list  
**Authentication:** Bearer Token or API Key required

**Request Body:**
```json
{
  "name": "Weekly Groceries",
  "is_public": false
}
```

**Validation:**
- `name`: 1-255 characters, required
- `is_public`: boolean, default false

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Weekly Groceries",
  "is_public": false,
  "creator": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "MEMBER",
    "is_active": true,
    "created_at": "2025-09-01T10:00:00Z",
    "updated_at": "2025-09-01T10:00:00Z"
  },
  "items": [],
  "created_at": "2025-09-27T10:00:00Z",
  "updated_at": "2025-09-27T10:00:00Z"
}
```

---

### PUT /shopping-lists/{list_id}
**Description:** Update shopping list metadata (name, visibility)  
**Authentication:** Bearer Token or API Key required  
**Access:** Public lists (any authenticated user) or private lists (creator only)

**Request Body:**
```json
{
  "name": "Updated List Name",
  "is_public": true
}
```

**Validation:**
- `name`: 1-255 characters, optional
- `is_public`: boolean, optional

**Response:** `200 OK` (same structure as create response)

**Error Responses:**
- `403 Forbidden`: User lacks permission to modify list
- `404 Not Found`: Shopping list not found or access denied

---

### DELETE /shopping-lists/{list_id}
**Description:** Delete a shopping list (soft delete)  
**Authentication:** Bearer Token or API Key required  
**Access:** Public lists (any authenticated user) or private lists (creator only)

**Response:** `204 No Content`

**Error Responses:**
- `403 Forbidden`: User lacks permission to delete list
- `404 Not Found`: Shopping list not found or access denied

---

### POST /shopping-lists/{list_id}/duplicate
**Description:** Duplicate a shopping list with all its items  
**Authentication:** Bearer Token or API Key required  
**Access:** Must be able to view the source list

**Request Body:**
```json
{
  "name": "Copy of Weekly Groceries",
  "is_public": false
}
```

**Validation:**
- `name`: 1-255 characters, required
- `is_public`: boolean, default false

**Response:** `201 Created`
```json
{
  "id": 2,
  "name": "Copy of Weekly Groceries",
  "is_public": false,
  "creator": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "MEMBER",
    "is_active": true,
    "created_at": "2025-09-01T10:00:00Z",
    "updated_at": "2025-09-01T10:00:00Z"
  },
  "items": [
    {
      "id": 3,
      "item": {
        "id": 10,
        "name": "Whole Milk",
        "description": "1 gallon whole milk",
        "upc": "123456789012",
        "default_storage_type": "refrigerator",
        "is_active": true,
        "uda_fetched": false,
        "uda_fetch_attempted": false,
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2025-09-01T10:00:00Z"
      },
      "quantity": 2,
      "created_at": "2025-09-27T12:00:00Z",
      "updated_at": "2025-09-27T12:00:00Z"
    }
  ],
  "created_at": "2025-09-27T12:00:00Z",
  "updated_at": "2025-09-27T12:00:00Z"
}
```

---

### POST /shopping-lists/{list_id}/items
**Description:** Add an item to a shopping list  
**Authentication:** Bearer Token or API Key required  
**Access:** Public lists (any authenticated user) or private lists (creator only)

**Request Body:**
```json
{
  "item_id": 10,
  "quantity": 2
}
```

**Validation:**
- `item_id`: integer, required (must reference existing item)
- `quantity`: integer > 0, required

**Response:** `201 Created`
```json
{
  "id": 1,
  "item": {
    "id": 10,
    "name": "Whole Milk",
    "description": "1 gallon whole milk",
    "upc": "123456789012",
    "default_storage_type": "refrigerator",
    "is_active": true,
    "uda_fetched": false,
    "uda_fetch_attempted": false,
    "created_at": "2025-09-01T10:00:00Z",
    "updated_at": "2025-09-01T10:00:00Z"
  },
  "quantity": 2,
  "created_at": "2025-09-27T10:15:00Z",
  "updated_at": "2025-09-27T10:15:00Z"
}
```

**Error Responses:**
- `403 Forbidden`: User lacks permission to modify list
- `404 Not Found`: Shopping list or item not found
- `409 Conflict`: Item already exists in shopping list

---

### PUT /shopping-lists/{list_id}/items/{item_id}
**Description:** Update the quantity of an item in a shopping list  
**Authentication:** Bearer Token or API Key required  
**Access:** Public lists (any authenticated user) or private lists (creator only)

**Request Body:**
```json
{
  "quantity": 3
}
```

**Validation:**
- `quantity`: integer > 0, required

**Response:** `200 OK` (same structure as add item response)

**Error Responses:**
- `403 Forbidden`: User lacks permission to modify list
- `404 Not Found`: Shopping list or item not found in list

---

### DELETE /shopping-lists/{list_id}/items/{item_id}
**Description:** Remove an item from a shopping list (soft delete)  
**Authentication:** Bearer Token or API Key required  
**Access:** Public lists (any authenticated user) or private lists (creator only)

**Response:** `204 No Content`

**Error Responses:**
- `403 Forbidden`: User lacks permission to modify list
- `404 Not Found`: Shopping list or item not found in list

---

### GET /shopping-lists/{list_id}/logs
**Description:** Get logs for a shopping list (change history)  
**Authentication:** Bearer Token or API Key required  
**Access:** Available to any user who can view the shopping list

**Query Parameters:**
- `skip` (int, default: 0): Number of logs to skip
- `limit` (int, default: 100): Number of logs to return (max: 1000)
- `action_type` (string, optional): Filter by action type

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "action_type": "item_added",
      "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "MEMBER",
        "is_active": true,
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2025-09-01T10:00:00Z"
      },
      "details": {
        "item_id": 10,
        "item_name": "Whole Milk",
        "quantity": 2
      },
      "timestamp": "2025-09-27T10:15:00Z"
    },
    {
      "id": 2,
      "action_type": "created",
      "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "MEMBER",
        "is_active": true,
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2025-09-01T10:00:00Z"
      },
      "details": {
        "list_name": "Weekly Groceries",
        "is_public": false
      },
      "timestamp": "2025-09-27T10:00:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 100
}
```

**Action Types:**
- `created`: Shopping list was created
- `updated`: Shopping list metadata was changed
- `deleted`: Shopping list was deleted
- `item_added`: Item was added to the list
- `item_updated`: Item quantity was changed
- `item_removed`: Item was removed from the list
- `duplicated`: Shopping list was duplicated from another list

---

## Backup & Restore

All backup endpoints are under `/backup/` and require **ADMIN** role.

### POST /backup/create/full
**Description:** Create full database backup  
**Authentication:** ADMIN required

**Response:** `200 OK`
```json
{
  "backup_size": 1024000,
  "timestamp": "2025-09-20T10:00:00Z",
  "tables_included": ["users", "items", "locations", "skus", "alerts", "log_entries"],
  "message": "Full backup created successfully"
}
```

---

### POST /backup/create/full/download
**Description:** Create and download full backup  
**Authentication:** ADMIN required

**Response:** `200 OK`
- **Content-Type:** `application/octet-stream`
- **Content-Disposition:** `attachment; filename="stocky_backup_YYYYMMDD_HHMMSS.sql.gz"`

---

### POST /backup/import/partial
**Description:** Import partial backup data  
**Authentication:** ADMIN required

**Request Body:**
```json
{
  "backup_data": "base64_encoded_gzipped_sql_data",
  "force": false
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Partial backup imported successfully",
  "tables_affected": ["items", "skus"],
  "records_imported": 150,
  "timestamp": "2025-09-20T10:00:00Z"
}
```

---

### POST /backup/import/full
**Description:** Import full backup (replaces database)  
**Authentication:** ADMIN required

**Request Body:**
```json
{
  "backup_data": "base64_encoded_gzipped_sql_data",
  "force": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Full backup restored successfully",
  "tables_affected": ["users", "items", "locations", "skus", "alerts", "log_entries"],
  "records_imported": 1000,
  "timestamp": "2025-09-20T10:00:00Z"
}
```

---

### POST /backup/upload/import/partial
**Description:** Upload and import partial backup file  
**Authentication:** ADMIN required

**Request:** Multipart form data
- `file`: SQL or gzipped SQL file
- `force`: boolean (optional)

---

### POST /backup/upload/import/full
**Description:** Upload and import full backup file  
**Authentication:** ADMIN required

**Request:** Multipart form data
- `file`: SQL or gzipped SQL file
- `force`: boolean (optional)

---

## Health Check

### GET /health
**Description:** API health check  
**Authentication:** None required

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "stocky-backend"
}
```

---

## Error Codes

### Standard HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data or validation errors
- **401 Unauthorized**: Authentication required or invalid credentials
- **403 Forbidden**: Access denied (insufficient permissions)
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server error

### Common Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### Authentication Errors

```json
{
  "detail": "Could not validate credentials",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Security (REQUIRED)
SECRET_KEY="your-32-character-hex-secret"  # Generate with: openssl rand -hex 32

# CORS (REQUIRED for web frontend)
ALLOWED_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Database (Optional, defaults to SQLite)
DATABASE_URL="sqlite+aiosqlite:///./data/stocky.db"
# or PostgreSQL: "postgresql://user:pass@host:port/dbname"

# Application (Optional)
DEBUG="false"                    # Set to "true" for development
HOST="0.0.0.0"                  # Server bind address
PORT="8000"                     # Server port

# External Services (Optional)
UDA_BASE_URL="https://uda-service.com"  # External UPC data service
UDA_TIMEOUT="5"                 # UDA service timeout in seconds

# Logging (Optional)
LOG_LEVEL="INFO"                # DEBUG, INFO, WARNING, ERROR
MAX_LOG_ENTRIES="10000"         # Maximum log entries to retain

# Token Settings (Optional)
ACCESS_TOKEN_EXPIRE_MINUTES="30"  # JWT expiration time
ALGORITHM="HS256"               # JWT algorithm
```

### Docker Deployment Example

```bash
docker run -d \
  --name stocky-backend \
  -p 8000:8000 \
  -v stocky-data:/app/data \
  -e SECRET_KEY="$(openssl rand -hex 32)" \
  -e ALLOWED_ORIGINS="https://stocky.yourdomain.com" \
  -e DEBUG="false" \
  your-registry/stocky-backend:latest
```

### Initial Setup

After deployment, create an admin user:

```bash
docker exec -it stocky-backend python scripts/initial_data.py
```

---

## Rate Limiting & Performance

- **Default request timeout:** 30 seconds
- **Maximum request body size:** 10MB (for file uploads)
- **Database connection pooling:** Enabled
- **Pagination:** Most list endpoints support `skip` and `limit` parameters

## Data Validation

All request bodies are validated using Pydantic models. Validation errors return:

```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "validation error message",
      "type": "validation_error_type"
    }
  ]
}
```

---

*Last updated: September 20, 2025*