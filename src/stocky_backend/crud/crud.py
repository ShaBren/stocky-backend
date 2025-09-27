"""
CRUD operations for database models
"""
from typing import List, Optional, Dict, Any, Generic, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel

from ..models.models import User, Item, Location, SKU, Alert, LogEntry, ShoppingList, ShoppingListItem, ShoppingListLog
from ..core.auth import hash_password
from ..schemas.schemas import (
    UserCreate, UserUpdate,
    ItemCreate, ItemUpdate, 
    LocationCreate, LocationUpdate,
    SKUCreate, SKUUpdate,
    AlertCreate, AlertUpdate,
    ShoppingListCreate, ShoppingListUpdate, ShoppingListDuplicate,
    ShoppingListItemCreate, ShoppingListItemUpdate
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


class ShoppingListCRUD(CRUDBase[ShoppingList, ShoppingListCreate, ShoppingListUpdate]):
    def __init__(self):
        super().__init__(ShoppingList)
    
    def get_accessible_lists(
        self,
        db: Session,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> tuple[List[ShoppingList], int]:
        """Get lists accessible to user (public + own private)"""
        query = db.query(ShoppingList).filter(
            or_(
                ShoppingList.is_public,
                ShoppingList.creator_id == current_user.id
            )
        )
        
        if not include_deleted:
            query = query.filter(~ShoppingList.is_deleted)
            
        total = query.count()
        lists = query.offset(skip).limit(limit).all()
        return lists, total
    
    def get_by_id_if_accessible(
        self,
        db: Session,
        list_id: int,
        current_user: User
    ) -> Optional[ShoppingList]:
        """Get list if user has access (public or owner)"""
        return db.query(ShoppingList).filter(
            and_(
                ShoppingList.id == list_id,
                ~ShoppingList.is_deleted,
                or_(
                    ShoppingList.is_public,
                    ShoppingList.creator_id == current_user.id
                )
            )
        ).first()
    
    def can_modify_list(
        self,
        shopping_list: ShoppingList,
        current_user: User
    ) -> bool:
        """Check if user can modify the list (collaborative editing rules)"""
        # Public lists: anyone can modify
        # Private lists: only creator can modify
        if shopping_list.is_public:
            return True
        return shopping_list.creator_id == current_user.id
    
    def create(
        self,
        db: Session,
        obj_in: ShoppingListCreate,
        creator: User
    ) -> ShoppingList:
        """Create new shopping list with logging"""
        obj_data = obj_in.model_dump()
        obj_data['creator_id'] = creator.id
        obj_data['is_deleted'] = False
        
        db_obj = ShoppingList(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Log the creation
        self.log_action(
            db,
            db_obj,
            creator,
            "created",
            {
                "list_name": db_obj.name,
                "is_public": db_obj.is_public
            }
        )
        
        return db_obj
    
    def update(
        self,
        db: Session,
        db_obj: ShoppingList,
        obj_in: ShoppingListUpdate,
        current_user: User
    ) -> ShoppingList:
        """Update shopping list with logging"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Track changes for logging
        changes = {}
        for field, new_value in update_data.items():
            old_value = getattr(db_obj, field)
            if old_value != new_value:
                changes[field] = {"from": old_value, "to": new_value}
                setattr(db_obj, field, new_value)
        
        if changes:
            db.commit()
            db.refresh(db_obj)
            
            # Log the update
            self.log_action(
                db,
                db_obj,
                current_user,
                "updated",
                {"changes": changes}
            )
        
        return db_obj
    
    def remove(
        self,
        db: Session,
        db_obj: ShoppingList,
        current_user: User
    ) -> ShoppingList:
        """Soft delete shopping list with logging"""
        db_obj.is_deleted = True
        db.commit()
        db.refresh(db_obj)
        
        # Log the deletion
        self.log_action(
            db,
            db_obj,
            current_user,
            "deleted",
            {"list_name": db_obj.name}
        )
        
        return db_obj
    
    def duplicate(
        self,
        db: Session,
        source_list: ShoppingList,
        duplicate_data: ShoppingListDuplicate,
        current_user: User
    ) -> ShoppingList:
        """Duplicate shopping list with all items"""
        # Create new list
        new_list_data = {
            "name": duplicate_data.name,
            "is_public": duplicate_data.is_public,
            "creator_id": current_user.id,
            "is_deleted": False
        }
        
        new_list = ShoppingList(**new_list_data)
        db.add(new_list)
        db.commit()
        db.refresh(new_list)
        
        # Copy all active items
        for source_item in source_list.items:
            if not source_item.is_deleted:
                new_item = ShoppingListItem(
                    shopping_list_id=new_list.id,
                    item_id=source_item.item_id,
                    quantity=source_item.quantity,
                    is_deleted=False
                )
                db.add(new_item)
        
        db.commit()
        
        # Log the duplication
        self.log_action(
            db,
            new_list,
            current_user,
            "duplicated",
            {
                "source_list_id": source_list.id,
                "source_list_name": source_list.name,
                "new_list_name": new_list.name
            }
        )
        
        return new_list
    
    def add_item(
        self,
        db: Session,
        shopping_list: ShoppingList,
        item_data: ShoppingListItemCreate,
        current_user: User
    ) -> ShoppingListItem:
        """Add item to shopping list with logging"""
        # Check if item already exists in list (including soft-deleted)
        existing_item = db.query(ShoppingListItem).filter(
            and_(
                ShoppingListItem.shopping_list_id == shopping_list.id,
                ShoppingListItem.item_id == item_data.item_id
            )
        ).first()
        
        if existing_item:
            if existing_item.is_deleted:
                # Restore the soft-deleted item
                existing_item.is_deleted = False
                existing_item.quantity = item_data.quantity
                db.commit()
                db.refresh(existing_item)
                
                # Log as item_added
                item_obj = db.query(Item).filter(Item.id == item_data.item_id).first()
                self.log_action(
                    db,
                    shopping_list,
                    current_user,
                    "item_added",
                    {
                        "item_id": item_data.item_id,
                        "item_name": item_obj.name if item_obj else "Unknown",
                        "quantity": item_data.quantity
                    }
                )
                
                return existing_item
            else:
                raise ValueError("Item already exists in shopping list")
        
        # Create new item
        obj_data = item_data.model_dump()
        obj_data['shopping_list_id'] = shopping_list.id
        obj_data['is_deleted'] = False
        
        db_obj = ShoppingListItem(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Log the addition
        item_obj = db.query(Item).filter(Item.id == item_data.item_id).first()
        self.log_action(
            db,
            shopping_list,
            current_user,
            "item_added",
            {
                "item_id": item_data.item_id,
                "item_name": item_obj.name if item_obj else "Unknown",
                "quantity": item_data.quantity
            }
        )
        
        return db_obj
    
    def update_item_quantity(
        self,
        db: Session,
        list_item: ShoppingListItem,
        new_quantity: int,
        current_user: User
    ) -> ShoppingListItem:
        """Update item quantity with logging"""
        old_quantity = list_item.quantity
        list_item.quantity = new_quantity
        db.commit()
        db.refresh(list_item)
        
        # Log the update
        item_obj = db.query(Item).filter(Item.id == list_item.item_id).first()
        shopping_list = db.query(ShoppingList).filter(ShoppingList.id == list_item.shopping_list_id).first()
        
        self.log_action(
            db,
            shopping_list,
            current_user,
            "item_updated",
            {
                "item_id": list_item.item_id,
                "item_name": item_obj.name if item_obj else "Unknown",
                "quantity": {"from": old_quantity, "to": new_quantity}
            }
        )
        
        return list_item
    
    def remove_item(
        self,
        db: Session,
        list_item: ShoppingListItem,
        current_user: User
    ) -> None:
        """Remove item from shopping list with logging (soft delete)"""
        # Log before deletion
        item_obj = db.query(Item).filter(Item.id == list_item.item_id).first()
        shopping_list = db.query(ShoppingList).filter(ShoppingList.id == list_item.shopping_list_id).first()
        
        self.log_action(
            db,
            shopping_list,
            current_user,
            "item_removed",
            {
                "item_id": list_item.item_id,
                "item_name": item_obj.name if item_obj else "Unknown",
                "quantity": list_item.quantity
            }
        )
        
        # Soft delete the item
        list_item.is_deleted = True
        db.commit()
    
    def get_list_item(
        self,
        db: Session,
        shopping_list_id: int,
        item_id: int
    ) -> Optional[ShoppingListItem]:
        """Get a specific item from a shopping list"""
        return db.query(ShoppingListItem).filter(
            and_(
                ShoppingListItem.shopping_list_id == shopping_list_id,
                ShoppingListItem.item_id == item_id,
                ~ShoppingListItem.is_deleted
            )
        ).first()
    
    def get_logs(
        self,
        db: Session,
        shopping_list_id: int,
        skip: int = 0,
        limit: int = 100,
        action_type: Optional[str] = None
    ) -> tuple[List[ShoppingListLog], int]:
        """Get logs for a shopping list"""
        query = db.query(ShoppingListLog).filter(
            ShoppingListLog.shopping_list_id == shopping_list_id
        ).order_by(ShoppingListLog.timestamp.desc())
        
        if action_type:
            query = query.filter(ShoppingListLog.action_type == action_type)
        
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        return logs, total
    
    def log_action(
        self,
        db: Session,
        shopping_list: ShoppingList,
        user: User,
        action_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> ShoppingListLog:
        """Log shopping list action"""
        import json
        
        log_entry = ShoppingListLog(
            shopping_list_id=shopping_list.id,
            user_id=user.id,
            action_type=action_type,
            details=json.dumps(details) if details else None
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry


# Create CRUD instances
user = UserCRUD()
item = ItemCRUD()
location = LocationCRUD()
sku = SKUCRUD()
alert = AlertCRUD()
log = LogEntryCRUD()
shopping_list = ShoppingListCRUD()
