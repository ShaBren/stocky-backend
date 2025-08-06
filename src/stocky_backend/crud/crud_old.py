"""
CRUD operations for database models
"""
from typing import List, Optional, Dict, Any, Generic, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel

from ..models.models import User, Item, Location, SKU, Alert, UserRole
from ..core.auth import hash_password
from ..schemas.schemas import (
    UserCreate, UserUpdate,
    ItemCreate, ItemUpdate, 
    LocationCreate, LocationUpdate,
    SKUCreate, SKUUpdate,
    AlertCreate, AlertUpdate
)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


# User CRUD operations
class UserCRUD:
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate, created_by_id: int) -> User:
        """Create a new user"""
        hashed_password = hash_password(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            role=user.role,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update an existing user"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Soft delete a user (set inactive)"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        
        db_user.is_active = False
        db.commit()
        return True


# Item CRUD operations
class ItemCRUD(CRUDBase[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(Item)

    def get_by_upc(self, db: Session, upc: str) -> Optional[Item]:
        """Get item by UPC"""
        return db.query(Item).filter(Item.upc == upc).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[Item]:
        """Get list of items"""
        query = db.query(Item)
        if not include_inactive:
            query = query.filter(Item.is_active)
        return query.offset(skip).limit(limit).all()
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> List[Item]:
        """Search items by name, description, or UPC"""
        search_term = f"%{query}%"
        return db.query(Item).filter(
            and_(
                Item.is_active,
                or_(
                    Item.name.ilike(search_term),
                    Item.description.ilike(search_term),
                    Item.upc.like(search_term)
                )
            )
        ).offset(skip).limit(limit).all()


# Location CRUD operations
class LocationCRUD:
    @staticmethod
    def get_location(db: Session, location_id: int) -> Optional[Location]:
        """Get location by ID"""
        return db.query(Location).filter(Location.id == location_id).first()
    
    @staticmethod
    def get_locations(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[Location]:
        """Get list of locations"""
        query = db.query(Location)
        if not include_inactive:
            query = query.filter(Location.is_active == True)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_location(db: Session, location: LocationCreate, created_by_id: int) -> Location:
        """Create a new location"""
        db_location = Location(
            name=location.name,
            description=location.description,
            storage_type=location.storage_type,
            created_by=created_by_id,
            is_active=True
        )
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location
    
    @staticmethod
    def update_location(db: Session, location_id: int, location_update: LocationUpdate) -> Optional[Location]:
        """Update an existing location"""
        db_location = db.query(Location).filter(Location.id == location_id).first()
        if not db_location:
            return None
        
        update_data = location_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_location, field, value)
        
        db.commit()
        db.refresh(db_location)
        return db_location


# SKU CRUD operations
class SKUCRUD:
    @staticmethod
    def get_sku(db: Session, sku_id: int) -> Optional[SKU]:
        """Get SKU by ID"""
        return db.query(SKU).filter(SKU.id == sku_id).first()
    
    @staticmethod
    def get_skus(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[SKU]:
        """Get list of SKUs"""
        query = db.query(SKU)
        if not include_inactive:
            query = query.filter(SKU.is_active == True)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_skus_by_item(db: Session, item_id: int) -> List[SKU]:
        """Get all SKUs for a specific item"""
        return db.query(SKU).filter(
            and_(SKU.item_id == item_id, SKU.is_active == True)
        ).all()
    
    @staticmethod
    def get_skus_by_location(db: Session, location_id: int) -> List[SKU]:
        """Get all SKUs in a specific location"""
        return db.query(SKU).filter(
            and_(SKU.location_id == location_id, SKU.is_active == True)
        ).all()
    
    @staticmethod
    def create_sku(db: Session, sku: SKUCreate, created_by_id: int) -> SKU:
        """Create a new SKU"""
        db_sku = SKU(
            item_id=sku.item_id,
            location_id=sku.location_id,
            quantity=sku.quantity,
            unit=sku.unit,
            expiry_date=sku.expiry_date,
            notes=sku.notes,
            created_by=created_by_id,
            is_active=True
        )
        db.add(db_sku)
        db.commit()
        db.refresh(db_sku)
        return db_sku
    
    @staticmethod
    def update_sku(db: Session, sku_id: int, sku_update: SKUUpdate) -> Optional[SKU]:
        """Update an existing SKU"""
        db_sku = db.query(SKU).filter(SKU.id == sku_id).first()
        if not db_sku:
            return None
        
        update_data = sku_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_sku, field, value)
        
        db.commit()
        db.refresh(db_sku)
        return db_sku


# Alert CRUD operations
class AlertCRUD:
    @staticmethod
    def get_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """Get alert by ID"""
        return db.query(Alert).filter(Alert.id == alert_id).first()
    
    @staticmethod
    def get_alerts(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Alert]:
        """Get list of alerts"""
        query = db.query(Alert)
        if active_only:
            query = query.filter(Alert.is_active == True)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_unacknowledged_alerts(db: Session) -> List[Alert]:
        """Get all unacknowledged active alerts"""
        return db.query(Alert).filter(
            and_(Alert.is_active == True, Alert.is_acknowledged == False)
        ).all()
    
    @staticmethod
    def create_alert(db: Session, alert: AlertCreate, created_by_id: int) -> Alert:
        """Create a new alert"""
        db_alert = Alert(
            alert_type=alert.alert_type,
            message=alert.message,
            threshold_value=alert.threshold_value,
            sku_id=alert.sku_id,
            created_by=created_by_id,
            is_active=True,
            is_acknowledged=False
        )
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert
    
    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """Acknowledge an alert"""
        db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not db_alert:
            return None
        
        db_alert.is_acknowledged = True
        db_alert.acknowledged_at = db.func.now()
        db.commit()
        db.refresh(db_alert)
        return db_alert


# Export all CRUD classes
user_crud = UserCRUD()
item_crud = ItemCRUD()
location_crud = LocationCRUD()
sku_crud = SKUCRUD()
alert_crud = AlertCRUD()
