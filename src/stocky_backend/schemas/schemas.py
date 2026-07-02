"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.models import StorageType, UserRole


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""

    model_config = ConfigDict(from_attributes=True)


# Authentication schemas
class Token(BaseModel):
    """JWT token response (legacy — sessions are now the primary auth method)"""

    access_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    """Session-based login response — no tokens in body, auth is via httpOnly cookie."""

    user_id: int
    username: str
    role: UserRole


class LoginRequest(BaseModel):
    """User login request"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    remember_me: bool = Field(default=False, description="Enable persistent session with cookies")


class PasswordChange(BaseModel):
    """Password change request"""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    """User creation request"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.MEMBER


class UserUpdate(BaseModel):
    """User update request"""

    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseSchema):
    """User response model"""

    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Item schemas
class ItemCreate(BaseModel):
    """Item creation request"""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    upc: str | None = Field(None, min_length=8, max_length=20)
    default_storage_type: StorageType | None = None
    upc_data: dict[str, Any] | None = None


class ItemUpdate(BaseModel):
    """Item update request"""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    upc: str | None = Field(None, min_length=8, max_length=20)
    default_storage_type: StorageType | None = None
    is_active: bool | None = None
    upc_data: dict[str, Any] | None = None


class ItemResponse(BaseSchema):
    """Item response model"""

    id: int
    name: str
    description: str | None
    upc: str | None
    default_storage_type: str | None
    is_active: bool
    uda_fetched: bool
    uda_fetch_attempted: bool
    upc_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


# Location schemas
class LocationCreate(BaseModel):
    """Location creation request"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    storage_type: StorageType


class LocationUpdate(BaseModel):
    """Location update request"""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    storage_type: StorageType | None = None
    is_active: bool | None = None


class LocationResponse(BaseSchema):
    """Location response model"""

    id: int
    name: str
    description: str | None
    storage_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# SKU schemas
class SKUCreate(BaseModel):
    """SKU creation request"""

    item_id: int
    location_id: int
    quantity: float = Field(..., ge=0)
    unit: str | None = Field(None, max_length=20)
    expiry_date: datetime | None = None
    notes: str | None = Field(None, max_length=1000)


class SKUUpdate(BaseModel):
    """SKU update request"""

    quantity: float | None = Field(None, ge=0)
    unit: str | None = Field(None, max_length=20)
    expiry_date: datetime | None = None
    notes: str | None = Field(None, max_length=1000)
    is_active: bool | None = None
    location_id: int | None = None


class SKUResponse(BaseSchema):
    """SKU response model"""

    id: int
    quantity: float
    unit: str | None
    expiry_date: datetime | None
    notes: str | None
    is_active: bool
    item_id: int
    location_id: int
    created_at: datetime
    updated_at: datetime


# Alert schemas
class AlertCreate(BaseModel):
    """Alert creation request"""

    alert_type: str = Field(..., max_length=50)
    message: str = Field(..., max_length=1000)
    threshold_value: float | None = None
    sku_id: int | None = None


class AlertUpdate(BaseModel):
    """Alert update request"""

    is_acknowledged: bool | None = None
    is_active: bool | None = None


class AlertResponse(BaseSchema):
    """Alert response model"""

    id: int
    alert_type: str
    message: str
    threshold_value: float | None
    is_active: bool
    is_acknowledged: bool
    acknowledged_at: datetime | None
    sku_id: int | None
    created_at: datetime
    updated_at: datetime


# Scanner schemas
class ScanRequest(BaseModel):
    """Scanner barcode scan request — accepts UPCs or command JSON."""

    upc: str = Field(..., min_length=1, max_length=500, description="Scanned value — UPC barcode or command JSON")
    scanner_id: str | None = None
    location_hint: str | None = None


class ScanResponse(BaseModel):
    """Scanner scan response"""

    success: bool
    item: ItemResponse | None = None
    skus: list[SKUResponse] = []
    message: str
    suggested_actions: list[str] = []
    mode: str | None = None
    scanner_state: dict[str, Any] | None = None


class ScannerCommand(BaseModel):
    """Parsed scanner command from a command barcode."""

    command: str
    payload: dict[str, Any] | None = None


class QRCommandRequest(BaseModel):
    """Request to generate a command QR code."""

    command: str
    payload: dict[str, Any] | None = None


class ScannerState(BaseModel):
    """Scanner state stored in the user's scanner_state JSON column."""

    current_mode: str = "add"
    current_location_id: int | None = None
    associated_ui_id: str | None = None
    last_scan_timestamp: str | None = None


class ScannerStatus(BaseModel):
    """Scanner status information"""

    scanner_id: str
    is_associated: bool
    associated_user: str | None = None
    last_seen: datetime


class SKUQuantityUpdate(BaseModel):
    """SKU quantity update request"""

    quantity: int = Field(..., ge=0)


# Search schemas
class SearchRequest(BaseModel):
    """Search request"""

    query: str = Field(..., min_length=1)
    item_types: list[str] | None = None
    location_filter: int | None = None
    include_inactive: bool = False


class SearchResponse(BaseModel):
    """Search response"""

    items: list[ItemResponse]
    total_count: int
    query: str


# Backup schemas
class BackupResponse(BaseModel):
    """Response for backup creation"""

    backup_size: int
    timestamp: datetime
    tables_included: list[str]
    message: str


class BackupImportRequest(BaseModel):
    """Request for backup import"""

    backup_data: str = Field(..., description="Base64 encoded gzipped SQL data")
    force: bool = Field(default=False, description="Force import even if it might cause data loss")


class BackupImportResponse(BaseModel):
    """Response for backup import"""

    success: bool
    message: str
    tables_affected: list[str]
    records_imported: int
    timestamp: datetime


# Shopping List schemas
class ShoppingListItemBase(BaseModel):
    """Base shopping list item schema"""

    item_id: int
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


class ShoppingListItemCreate(ShoppingListItemBase):
    """Shopping list item creation request"""

    pass


class ShoppingListItemUpdate(BaseModel):
    """Shopping list item update request"""

    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


class ShoppingListItemResponse(BaseSchema):
    """Shopping list item response model"""

    id: int
    item: ItemResponse
    quantity: int
    created_at: datetime
    updated_at: datetime


class ShoppingListBase(BaseModel):
    """Base shopping list schema"""

    name: str = Field(min_length=1, max_length=255, description="List name")
    is_public: bool = Field(default=False, description="Whether list is public")


class ShoppingListCreate(ShoppingListBase):
    """Shopping list creation request"""

    pass


class ShoppingListUpdate(BaseModel):
    """Shopping list update request"""

    name: str | None = Field(None, min_length=1, max_length=255)
    is_public: bool | None = None


class ShoppingListDuplicate(BaseModel):
    """Shopping list duplication request"""

    name: str = Field(min_length=1, max_length=255, description="Name for duplicated list")
    is_public: bool = Field(default=False, description="Whether duplicated list should be public")


class ShoppingListSummary(BaseSchema):
    """Shopping list summary response model (for list views)"""

    id: int
    name: str
    is_public: bool
    creator: UserResponse
    item_count: int
    created_at: datetime
    updated_at: datetime


class ShoppingListResponse(BaseSchema):
    """Shopping list detailed response model"""

    id: int
    name: str
    is_public: bool
    creator: UserResponse
    items: list[ShoppingListItemResponse]
    created_at: datetime
    updated_at: datetime


class ShoppingListLogResponse(BaseSchema):
    """Shopping list log response model"""

    id: int
    action_type: str
    user: UserResponse
    details: dict[str, Any] | None = None
    timestamp: datetime


class PaginatedShoppingListsResponse(BaseModel):
    """Paginated shopping lists response"""

    items: list[ShoppingListSummary]
    total: int
    skip: int
    limit: int


class PaginatedShoppingListLogsResponse(BaseModel):
    """Paginated shopping list logs response"""

    items: list[ShoppingListLogResponse]
    total: int
    skip: int
    limit: int
