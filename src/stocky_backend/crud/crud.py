"""
CRUD operations for database models
"""
from typing import List, Optional, Dict, Any, Generic, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel

from ..models.models import User, Item, Location, SKU, Alert, LogEntry
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

    def create(self, db: Session, *, obj_in: CreateSchemaType | dict) -> ModelType:
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump()
        elif isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            raise TypeError("obj_in must be a Pydantic model or dict")
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
        obj = db.get(self.model, id)
        db.delete(obj)
        db.commit()
        return obj


class UserCRUD(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        obj_data = obj_in.model_dump()
        obj_data['hashed_password'] = hash_password(obj_data.pop('password'))
        obj_data['is_active'] = True
        db_obj = User(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ItemCRUD(CRUDBase[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(Item)

    def get_by_upc(self, db: Session, upc: str) -> Optional[Item]:
        return db.query(Item).filter(Item.upc == upc).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[Item]:
        query = db.query(Item)
        if not include_inactive:
            query = query.filter(Item.is_active)
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: ItemCreate, created_by_id: int = 1) -> Item:
        obj_data = obj_in.model_dump()
        obj_data['created_by'] = created_by_id
        obj_data['is_active'] = True
        obj_data['uda_fetched'] = False
        obj_data['uda_fetch_attempted'] = False
        db_obj = Item(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> List[Item]:
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


class LocationCRUD(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def __init__(self):
        super().__init__(Location)

    def get_by_name(self, db: Session, name: str) -> Optional[Location]:
        return db.query(Location).filter(Location.name == name).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[Location]:
        query = db.query(Location)
        if not include_inactive:
            query = query.filter(Location.is_active)
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: LocationCreate, created_by_id: int = 1) -> Location:
        obj_data = obj_in.model_dump()
        obj_data['created_by'] = created_by_id
        obj_data['is_active'] = True
        db_obj = Location(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> List[Location]:
        search_term = f"%{query}%"
        return db.query(Location).filter(
            and_(
                Location.is_active,
                or_(
                    Location.name.ilike(search_term),
                    Location.description.ilike(search_term)
                )
            )
        ).offset(skip).limit(limit).all()


class SKUCRUD(CRUDBase[SKU, SKUCreate, SKUUpdate]):
    def __init__(self):
        super().__init__(SKU)

    def get_by_item(self, db: Session, item_id: int, skip: int = 0, limit: int = 100) -> List[SKU]:
        return db.query(SKU).filter(
            and_(SKU.item_id == item_id, SKU.is_active)
        ).offset(skip).limit(limit).all()
    
    def get_by_location(self, db: Session, location_id: int, skip: int = 0, limit: int = 100) -> List[SKU]:
        return db.query(SKU).filter(
            and_(SKU.location_id == location_id, SKU.is_active)
        ).offset(skip).limit(limit).all()
    
    def get_by_item_location(self, db: Session, item_id: int, location_id: int) -> Optional[SKU]:
        return db.query(SKU).filter(
            and_(
                SKU.item_id == item_id,
                SKU.location_id == location_id,
                SKU.is_active
            )
        ).first()
    
    def get_low_stock(self, db: Session, skip: int = 0, limit: int = 100, threshold: float = 5.0) -> List[SKU]:
        return db.query(SKU).filter(
            and_(
                SKU.is_active,
                SKU.quantity <= threshold
            )
        ).offset(skip).limit(limit).all()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[SKU]:
        query = db.query(SKU)
        if not include_inactive:
            query = query.filter(SKU.is_active)
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: SKUCreate, created_by_id: int = 1) -> SKU:
        obj_data = obj_in.model_dump()
        obj_data['created_by'] = created_by_id
        obj_data['is_active'] = True
        db_obj = SKU(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> List[SKU]:
        search_term = f"%{query}%"
        return db.query(SKU).join(Item).join(Location).filter(
            and_(
                SKU.is_active,
                or_(
                    Item.name.ilike(search_term),
                    Item.upc.like(search_term),
                    Location.name.ilike(search_term)
                )
            )
        ).offset(skip).limit(limit).all()
    
    def update_quantity(self, db: Session, sku_id: int, new_quantity: int) -> Optional[SKU]:
        sku = db.query(SKU).filter(SKU.id == sku_id).first()
        if sku:
            sku.quantity = new_quantity
            db.commit()
            db.refresh(sku)
        return sku


class AlertCRUD(CRUDBase[Alert, AlertCreate, AlertUpdate]):
    def __init__(self):
        super().__init__(Alert)

    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
        return db.query(Alert).filter(
            and_(Alert.is_active, ~Alert.is_acknowledged)
        ).offset(skip).limit(limit).all()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[Alert]:
        query = db.query(Alert)
        if not include_inactive:
            query = query.filter(Alert.is_active)
        return query.offset(skip).limit(limit).all()


class LogEntryCRUD(CRUDBase[LogEntry, None, None]):
    def __init__(self):
        super().__init__(LogEntry)

    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[LogEntry]:
        return db.query(LogEntry).filter(
            LogEntry.user_id == user_id
        ).order_by(LogEntry.timestamp.desc()).offset(skip).limit(limit).all()
    
    def get_by_action(self, db: Session, action: str, skip: int = 0, limit: int = 100) -> List[LogEntry]:
        return db.query(LogEntry).filter(
            LogEntry.action == action
        ).order_by(LogEntry.timestamp.desc()).offset(skip).limit(limit).all()


# Create CRUD instances
user = UserCRUD()
item = ItemCRUD()
location = LocationCRUD()
sku = SKUCRUD()
alert = AlertCRUD()
log = LogEntryCRUD()
