"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.models import UserRole, StorageType


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


# Authentication schemas
class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    role: UserRole
    refresh_token: str


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """User login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    """User creation request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.MEMBER


class UserUpdate(BaseModel):
    """User update request"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


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
    description: Optional[str] = Field(None, max_length=1000)
    upc: Optional[str] = Field(None, min_length=8, max_length=20)
    default_storage_type: Optional[StorageType] = None


class ItemUpdate(BaseModel):
    """Item update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    upc: Optional[str] = Field(None, min_length=8, max_length=20)
    default_storage_type: Optional[StorageType] = None
    is_active: Optional[bool] = None


class ItemResponse(BaseSchema):
    """Item response model"""
    id: int
    name: str
    description: Optional[str]
    upc: Optional[str]
    default_storage_type: Optional[str]
    is_active: bool
    uda_fetched: bool
    uda_fetch_attempted: bool
    created_at: datetime
    updated_at: datetime


# Location schemas
class LocationCreate(BaseModel):
    """Location creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    storage_type: StorageType


class LocationUpdate(BaseModel):
    """Location update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    storage_type: Optional[StorageType] = None
    is_active: Optional[bool] = None


class LocationResponse(BaseSchema):
    """Location response model"""
    id: int
    name: str
    description: Optional[str]
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
    unit: Optional[str] = Field(None, max_length=20)
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)


class SKUUpdate(BaseModel):
    """SKU update request"""
    quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    location_id: Optional[int] = None


class SKUResponse(BaseSchema):
    """SKU response model"""
    id: int
    quantity: float
    unit: Optional[str]
    expiry_date: Optional[datetime]
    notes: Optional[str]
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
    threshold_value: Optional[float] = None
    sku_id: Optional[int] = None


class AlertUpdate(BaseModel):
    """Alert update request"""
    is_acknowledged: Optional[bool] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseSchema):
    """Alert response model"""
    id: int
    alert_type: str
    message: str
    threshold_value: Optional[float]
    is_active: bool
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    sku_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# Scanner schemas
class ScanRequest(BaseModel):
    """Scanner barcode scan request"""
    upc: str = Field(..., min_length=8, max_length=20)
    scanner_id: Optional[str] = None
    location_hint: Optional[str] = None


class ScanResponse(BaseModel):
    """Scanner scan response"""
    success: bool
    item: Optional[ItemResponse] = None
    skus: List[SKUResponse] = []
    message: str
    suggested_actions: List[str] = []


class ScannerStatus(BaseModel):
    """Scanner status information"""
    scanner_id: str
    is_associated: bool
    associated_user: Optional[str] = None
    last_seen: datetime


class ScannerAssociation(BaseModel):
    """Scanner association request"""
    scanner_id: str
    user_id: Optional[str] = None


class SKUQuantityUpdate(BaseModel):
    """SKU quantity update request"""
    quantity: int = Field(..., ge=0)


# Search schemas
class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., min_length=1)
    item_types: Optional[List[str]] = None
    location_filter: Optional[int] = None
    include_inactive: bool = False


class SearchResponse(BaseModel):
    """Search response"""
    items: List[ItemResponse]
    total_count: int
    query: str


# Backup schemas
class BackupResponse(BaseModel):
    """Response for backup creation"""
    backup_size: int
    timestamp: datetime
    tables_included: List[str]
    message: str


class BackupImportRequest(BaseModel):
    """Request for backup import"""
    backup_data: str = Field(..., description="Base64 encoded gzipped SQL data")
    force: bool = Field(default=False, description="Force import even if it might cause data loss")


class BackupImportResponse(BaseModel):
    """Response for backup import"""
    success: bool
    message: str
    tables_affected: List[str]
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
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_public: Optional[bool] = None


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
    items: List[ShoppingListItemResponse]
    created_at: datetime
    updated_at: datetime


class ShoppingListLogResponse(BaseSchema):
    """Shopping list log response model"""
    id: int
    action_type: str
    user: UserResponse
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class PaginatedShoppingListsResponse(BaseModel):
    """Paginated shopping lists response"""
    items: List[ShoppingListSummary]
    total: int
    skip: int
    limit: int


class PaginatedShoppingListLogsResponse(BaseModel):
    """Paginated shopping list logs response"""
    items: List[ShoppingListLogResponse]
    total: int
    skip: int
    limit: int
