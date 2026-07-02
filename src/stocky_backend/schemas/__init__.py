"""
Schemas module for Stocky Backend
"""

from .schemas import (
    # Alerts
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    # Items
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    # Locations
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    QRCommandRequest,
    ScanRequest,
    ScanResponse,
    ScannerCommand,
    ScannerState,
    ScannerStatus,
    # Search
    SearchRequest,
    SearchResponse,
    # SKUs
    SKUCreate,
    SKUResponse,
    SKUUpdate,
    # Authentication
    LoginRequest,
    PasswordChange,
    SessionResponse,
    Token,
    # Users
    UserCreate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Authentication
    "Token",
    "LoginRequest",
    "SessionResponse",
    "PasswordChange",
    # Users
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Items
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    # Locations
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    # SKUs
    "SKUCreate",
    "SKUUpdate",
    "SKUResponse",
    # Alerts
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    # Scanner
    "ScanRequest",
    "ScanResponse",
    "ScannerCommand",
    "ScannerState",
    "ScannerStatus",
    "QRCommandRequest",
    # Search
    "SearchRequest",
    "SearchResponse",
]
