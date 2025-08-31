"""
Database models for the Stocky Backend application
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from ..db.database import Base


class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    MEMBER = "member" 
    SCANNER = "scanner"
    READ_ONLY = "read_only"


class StorageType(str, Enum):
    """Storage types for items"""
    PANTRY = "pantry"
    REFRIGERATOR = "refrigerator"
    FREEZER = "freezer"
    COUNTER = "counter"
    OTHER = "other"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.MEMBER)
    is_active = Column(Boolean, default=True)
    api_key = Column(String(255), unique=True, index=True, nullable=True)
    
    # JSON field for scanner users' flexible state management
    scanner_state = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    created_items = relationship("Item", back_populates="created_by_user")
    created_locations = relationship("Location", back_populates="created_by_user")
    created_skus = relationship("SKU", back_populates="created_by_user")
    created_alerts = relationship("Alert", back_populates="created_by_user")
    
    def __str__(self):
        return f"<User {self.username}>"


class Location(Base):
    """Location model for where items are stored"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    storage_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Foreign keys
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User", back_populates="created_locations")
    skus = relationship("SKU", back_populates="location")


class Item(Base):
    """Item model for products/goods"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    upc = Column(String(20), unique=True, index=True, nullable=True)
    default_storage_type = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # UDA (Universal Data Application) integration fields
    uda_fetched = Column(Boolean, default=False)
    uda_fetch_attempted = Column(Boolean, default=False)
    
    # Foreign keys
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User", back_populates="created_items")
    skus = relationship("SKU", back_populates="item")


class SKU(Base):
    """SKU (inventory) model linking items to locations with quantities"""
    __tablename__ = "skus"
    
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(20), nullable=True)  # e.g., "pieces", "lbs", "oz"
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Foreign keys
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    item = relationship("Item", back_populates="skus")
    location = relationship("Location", back_populates="skus")
    created_by_user = relationship("User", back_populates="created_skus")
    alerts = relationship("Alert", back_populates="sku")


class Alert(Base):
    """Alert model for low inventory, expiry warnings, etc."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)  # "low_stock", "expiry_warning", "custom"
    message = Column(Text, nullable=False)
    threshold_value = Column(Float, nullable=True)  # For low stock alerts
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    sku_id = Column(Integer, ForeignKey("skus.id"), nullable=True)  # Nullable for system-wide alerts
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sku = relationship("SKU", back_populates="alerts")
    created_by_user = relationship("User", back_populates="created_alerts")


class LogEntry(Base):
    """Log entry model for application logging"""
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_id = Column(String(50), nullable=True)  # For request tracking
    
    # Additional context data
    extra_data = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
