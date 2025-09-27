# Shopping Lists Feature Design Document

**Created:** September 27, 2025  
**Status:** Design Phase - Awaiting Review  
**Author:** AI Assistant  

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements Analysis](#requirements-analysis)
3. [Database Design](#database-design)
4. [API Design](#api-design)
5. [Business Logic Design](#business-logic-design)
6. [Security Considerations](#security-considerations)
7. [Integration Points](#integration-points)
8. [Implementation Plan](#implementation-plan)

---

## Overview

The Shopping Lists feature allows users to create, manage, and share shopping lists containing items from the inventory system. Lists can be public (shared with all users) or private (visible only to the creator), with full audit logging of all changes.

### Key Features
- **List Management**: Create, read, update, delete shopping lists
- **Visibility Control**: Public vs. private list visibility
- **Item Management**: Add/remove items with quantities (must reference existing inventory items)
- **Audit Logging**: Complete change history with user attribution
- **List Duplication**: Clone existing lists for reuse
- **Access Control**: Users can only see public lists or their own private lists

---

## Requirements Analysis

### Functional Requirements

1. **List CRUD Operations**
   - ✅ Create new shopping list (name, visibility, creator)
   - ✅ Read shopping lists (filtered by visibility and ownership)
   - ✅ Update shopping list metadata (name, visibility)
   - ✅ Delete shopping list (with cascade to items and logs)

2. **Item Management**
   - ✅ Add items to shopping list (item_id, quantity)
   - ✅ Update item quantities in shopping list
   - ✅ Remove items from shopping list
   - ✅ Validate items exist in inventory before adding

3. **Visibility & Access Control**
   - ✅ Set list as public or private on creation
   - ✅ Change visibility after creation
   - ✅ Filter lists by visibility (public + user's private lists)

4. **Audit & Logging**
   - ✅ Log all list changes (create, update, delete)
   - ✅ Log all item changes (add, update, remove)
   - ✅ Track user making each change
   - ✅ Timestamp all changes

5. **List Operations**
   - ✅ Duplicate existing shopping list
   - ✅ Preserve or modify visibility when duplicating

### Non-Functional Requirements

1. **Performance**
   - Efficient queries for list retrieval with proper indexing
   - Minimal database calls for list operations

2. **Security**
   - Proper authorization checks for list access
   - Validation of item references
   - Audit trail for compliance

3. **Scalability**
   - Support for large numbers of lists and items per list
   - Efficient pagination for list endpoints

---

## Database Design

### New Tables

#### `shopping_lists` Table
```sql
CREATE TABLE shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    creator_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    FOREIGN KEY (creator_id) REFERENCES users (id),
    INDEX idx_shopping_lists_creator (creator_id),
    INDEX idx_shopping_lists_public (is_public),
    INDEX idx_shopping_lists_deleted (is_deleted)
);
```

#### `shopping_list_items` Table
```sql
CREATE TABLE shopping_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shopping_list_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists (id),
    FOREIGN KEY (item_id) REFERENCES items (id),
    UNIQUE KEY unique_list_item (shopping_list_id, item_id),
    INDEX idx_shopping_list_items_list (shopping_list_id),
    INDEX idx_shopping_list_items_item (item_id),
    INDEX idx_shopping_list_items_deleted (is_deleted)
);
```

#### `shopping_list_logs` Table
```sql
CREATE TABLE shopping_list_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shopping_list_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- 'created', 'updated', 'deleted', 'item_added', 'item_updated', 'item_removed', 'duplicated'
    details TEXT, -- JSON string with change details
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id),
    INDEX idx_shopping_list_logs_list (shopping_list_id),
    INDEX idx_shopping_list_logs_user (user_id),
    INDEX idx_shopping_list_logs_action (action_type),
    INDEX idx_shopping_list_logs_timestamp (timestamp)
);
```

### SQLAlchemy Models

```python
# In src/stocky_backend/models/models.py

class ShoppingList(Base):
    __tablename__ = "shopping_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="shopping_lists")
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")
    logs = relationship("ShoppingListLog", back_populates="shopping_list", cascade="all, delete-orphan")


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"
    
    id = Column(Integer, primary_key=True, index=True)
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    item = relationship("Item")
    
    # Constraints
    __table_args__ = (UniqueConstraint('shopping_list_id', 'item_id', name='unique_list_item'),)


class ShoppingListLog(Base):
    __tablename__ = "shopping_list_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    details = Column(Text)  # JSON string
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="logs")
    user = relationship("User")


# Add to User model
class User(Base):
    # ... existing fields ...
    shopping_lists = relationship("ShoppingList", back_populates="creator")
```

---

## API Design

### Endpoint Structure: `/api/v1/shopping-lists`

#### 1. List Shopping Lists
```http
GET /api/v1/shopping-lists
```

**Query Parameters:**
- `skip` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Pagination limit (default: 100, max: 1000)
- `include_deleted` (bool, optional): Include deleted lists (admin only, default: false)

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
                "full_name": "John Doe"
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

#### 2. Get Shopping List Details
```http
GET /api/v1/shopping-lists/{list_id}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Weekly Groceries",
    "is_public": true,
    "creator": {
        "id": 1,
        "username": "john_doe",
        "full_name": "John Doe"
    },
    "items": [
        {
            "id": 1,
            "item": {
                "id": 10,
                "name": "Whole Milk",
                "upc": "123456789012"
            },
            "quantity": 2,
            "added_at": "2025-09-27T10:15:00Z"
        }
    ],
    "created_at": "2025-09-27T10:00:00Z",
    "updated_at": "2025-09-27T11:30:00Z"
}
```

#### 3. Create Shopping List
```http
POST /api/v1/shopping-lists
```

**Request Body:**
```json
{
    "name": "Weekly Groceries",
    "is_public": false
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "name": "Weekly Groceries",
    "is_public": false,
    "creator": {
        "id": 1,
        "username": "john_doe",
        "full_name": "John Doe"
    },
    "items": [],
    "created_at": "2025-09-27T10:00:00Z",
    "updated_at": "2025-09-27T10:00:00Z"
}
```

#### 4. Update Shopping List
```http
PUT /api/v1/shopping-lists/{list_id}
```

**Request Body:**
```json
{
    "name": "Updated List Name",
    "is_public": true
}
```

**Response:** `200 OK` (same structure as create response)

#### 5. Delete Shopping List
```http
DELETE /api/v1/shopping-lists/{list_id}
```

**Response:** `204 No Content`

#### 6. Duplicate Shopping List
```http
POST /api/v1/shopping-lists/{list_id}/duplicate
```

**Request Body:**
```json
{
    "name": "Copy of Weekly Groceries",
    "is_public": false
}
```

**Response:** `201 Created` (same structure as create response)

#### 7. Add Item to Shopping List
```http
POST /api/v1/shopping-lists/{list_id}/items
```

**Request Body:**
```json
{
    "item_id": 10,
    "quantity": 2
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "item": {
        "id": 10,
        "name": "Whole Milk",
        "upc": "123456789012"
    },
    "quantity": 2,
    "added_at": "2025-09-27T10:15:00Z"
}
```

#### 8. Update Item Quantity
```http
PUT /api/v1/shopping-lists/{list_id}/items/{item_id}
```

**Request Body:**
```json
{
    "quantity": 3
}
```

**Response:** `200 OK` (same structure as add item response)

#### 9. Remove Item from Shopping List
```http
DELETE /api/v1/shopping-lists/{list_id}/items/{item_id}
```

**Response:** `204 No Content`

#### 10. Get Shopping List Logs
```http
GET /api/v1/shopping-lists/{list_id}/logs
```

**Access:** Available to any user who can view the shopping list (for GUI change log display)

**Query Parameters:**
- `skip` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Pagination limit (default: 100)
- `action_type` (str, optional): Filter by action type

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
                "full_name": "John Doe"
            },
            "details": {
                "item_id": 10,
                "item_name": "Whole Milk",
                "quantity": 2
            },
            "timestamp": "2025-09-27T10:15:00Z"
        }
    ],
    "total": 1,
    "skip": 0,
    "limit": 100
}
```

---

## Business Logic Design

### Pydantic Schemas

```python
# In src/stocky_backend/schemas/schemas.py

class ShoppingListItemBase(BaseModel):
    item_id: int
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")

class ShoppingListItemCreate(ShoppingListItemBase):
    pass

class ShoppingListItemUpdate(BaseModel):
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")

class ShoppingListItemResponse(BaseModel):
    id: int
    item: ItemResponse
    quantity: int
    added_at: datetime

    class Config:
        from_attributes = True

class ShoppingListBase(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="List name")
    is_public: bool = Field(default=False, description="Whether list is public")

class ShoppingListCreate(ShoppingListBase):
    pass

class ShoppingListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_public: Optional[bool] = None

class ShoppingListDuplicate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Name for duplicated list")
    is_public: bool = Field(default=False, description="Whether duplicated list should be public")

class ShoppingListSummary(BaseModel):
    id: int
    name: str
    is_public: bool
    creator: UserResponse
    item_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShoppingListResponse(ShoppingListSummary):
    items: List[ShoppingListItemResponse]

class ShoppingListLogResponse(BaseModel):
    id: int
    action_type: str
    user: UserResponse
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
```

### CRUD Operations

```python
# In src/stocky_backend/crud/crud.py

class ShoppingListCRUD:
    def get_accessible_lists(
        self,
        db: Session,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> Tuple[List[ShoppingList], int]:
        """Get lists accessible to user (public + own private)"""
        
    def get_by_id_if_accessible(
        self,
        db: Session,
        list_id: int,
        current_user: User
    ) -> Optional[ShoppingList]:
        """Get list if user has access (public or owner)"""
        
    def create(
        self,
        db: Session,
        obj_in: ShoppingListCreate,
        creator: User
    ) -> ShoppingList:
        """Create new shopping list with logging"""
        
    def update(
        self,
        db: Session,
        db_obj: ShoppingList,
        obj_in: ShoppingListUpdate,
        current_user: User
    ) -> ShoppingList:
        """Update shopping list with logging"""
        
    def duplicate(
        self,
        db: Session,
        source_list: ShoppingList,
        duplicate_data: ShoppingListDuplicate,
        current_user: User
    ) -> ShoppingList:
        """Duplicate shopping list with all items"""
        
    def add_item(
        self,
        db: Session,
        shopping_list: ShoppingList,
        item_data: ShoppingListItemCreate,
        current_user: User
    ) -> ShoppingListItem:
        """Add item to shopping list with logging"""
        
    def update_item(
        self,
        db: Session,
        list_item: ShoppingListItem,
        quantity: int,
        current_user: User
    ) -> ShoppingListItem:
        """Update item quantity with logging"""
        
    def remove_item(
        self,
        db: Session,
        list_item: ShoppingListItem,
        current_user: User
    ) -> None:
        """Remove item from shopping list with logging"""
        
    def log_action(
        self,
        db: Session,
        shopping_list: ShoppingList,
        user: User,
        action_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> ShoppingListLog:
        """Log shopping list action"""
```

---

## Security Considerations

### Access Control Rules

1. **List Visibility**
   - Users can view all public lists
   - Users can view their own private lists
   - Users cannot view other users' private lists
   - Admins can view all lists (including with `include_deleted=true`)

2. **List Modification**
   - Any user who can view a list can modify it (collaborative editing)
   - Public lists: All authenticated users can modify
   - Private lists: Only the creator can modify
   - Admins can modify any list

3. **Validation**
   - Items must exist in the database before being added to lists
   - Quantities must be positive integers
   - List names must be non-empty and within length limits

4. **Audit Trail**
   - All changes are logged with user attribution
   - Logs are immutable (no update/delete operations)
   - Sensitive operations require authentication

### Log Detail Schema

The `details` field in `shopping_list_logs` follows this JSON schema:

```python
# Action: created
{
    "list_name": "Weekly Groceries",
    "is_public": false
}

# Action: updated  
{
    "changes": {
        "name": {"from": "Old Name", "to": "New Name"},
        "is_public": {"from": false, "to": true}
    }
}

# Action: deleted
{
    "list_name": "Weekly Groceries"
}

# Action: item_added
{
    "item_id": 10,
    "item_name": "Whole Milk", 
    "quantity": 2
}

# Action: item_updated
{
    "item_id": 10,
    "item_name": "Whole Milk",
    "quantity": {"from": 2, "to": 3}
}

# Action: item_removed
{
    "item_id": 10,
    "item_name": "Whole Milk",
    "quantity": 2
}

# Action: duplicated
{
    "source_list_id": 5,
    "source_list_name": "Original List",
    "new_list_name": "Copy of Original List"
}
```

### Error Handling

- `404 Not Found`: List doesn't exist or user lacks access
- `400 Bad Request`: Invalid input data
- `403 Forbidden`: User lacks permission to perform action
- `409 Conflict`: Item already exists in list (on add)
- `422 Validation Error`: Pydantic validation failures

---

## Integration Points

### Database Migrations
- Alembic migration to create the three new tables
- Foreign key constraints to existing `users` and `items` tables
- Proper indexing for performance

### Existing Systems Integration
- **Authentication**: Uses existing JWT/API key authentication
- **User Management**: References existing `User` model
- **Item Catalog**: References existing `Item` model
- **Logging**: Integrates with existing logging patterns
- **API Structure**: Follows existing FastAPI patterns

### Dependencies
- No new external dependencies required
- Uses existing SQLAlchemy, Pydantic, FastAPI stack

---

## Implementation Plan

### Phase 1: Database Layer
1. Create SQLAlchemy models for the three new tables
2. Generate Alembic migration
3. Add relationship fields to existing `User` model

### Phase 2: Schemas & CRUD
1. Create Pydantic schemas for all request/response types
2. Implement CRUD operations with proper access control
3. Add comprehensive logging functionality

### Phase 3: API Endpoints
1. Create `/api/v1/shopping-lists` endpoint file
2. Implement all 10 REST endpoints
3. Add proper error handling and validation

### Phase 4: Testing
1. Unit tests for CRUD operations
2. API endpoint tests
3. Integration tests for access control
4. End-to-end workflow tests

### Phase 5: Documentation
1. Update API reference documentation
2. Add shopping lists to source code structure docs
3. Create user documentation for the feature

---

## Open Questions & Design Decisions

### 1. List Item Uniqueness
**Decision:** Each item can appear only once per list (enforced by unique constraint)
**Rationale:** Simpler logic, update quantity instead of duplicate entries
**Alternative:** Allow duplicate items with different entries

### 2. Soft Delete vs. Hard Delete
**Decision:** Use soft delete for all operations (shopping lists and items)
**Rationale:** Preserves complete audit trail and allows recovery
**Note:** Both lists and list items use soft delete with is_deleted flags

### 3. Quantity Validation
**Decision:** Quantities must be positive integers
**Rationale:** Negative quantities don't make sense for shopping
**Note:** Zero quantities result in item removal

### 4. Log Detail Format
**Decision:** Store log details as JSON text with well-defined schema
**Rationale:** Flexible structure, easy to extend, structured for GUI consumption
**Schema:** Defined below in Log Detail Schema section

### 5. Public List Modification
**Decision:** Any user who can view a list can modify it (collaborative editing)
**Rationale:** Enables collaborative shopping list management
**Access Rule:** Public lists = all authenticated users can edit, Private lists = creator only

---

## Success Metrics

1. **Functionality**: All requirements implemented and tested
2. **Performance**: List operations complete within 200ms
3. **Security**: All access control rules properly enforced
4. **Usability**: Clear error messages and intuitive API design
5. **Maintainability**: Code follows existing patterns and is well-documented

---

*This design document is ready for review and feedback before implementation begins.*