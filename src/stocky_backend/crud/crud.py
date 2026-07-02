"""
CRUD operations for database models
"""

import hashlib
from datetime import UTC, datetime

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..core.auth import hash_password
from ..core.config import settings
from ..models.models import (
    SKU,
    Alert,
    Item,
    Location,
    LogEntry,
    Session as SessionModel,
    ShoppingList,
    ShoppingListItem,
    ShoppingListLog,
    User,
)
from ..schemas.schemas import (
    AlertCreate,
    AlertUpdate,
    ItemCreate,
    ItemUpdate,
    LocationCreate,
    LocationUpdate,
    ShoppingListCreate,
    ShoppingListDuplicate,
    ShoppingListItemCreate,
    ShoppingListUpdate,
    SKUCreate,
    SKUUpdate,
    UserCreate,
    UserUpdate,
)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id: int) -> ModelType | None:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType | dict) -> ModelType:
        if hasattr(obj_in, "model_dump"):
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
        obj_in: UpdateSchemaType | dict[str, Any],
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

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        obj_data = obj_in.model_dump()
        obj_data["hashed_password"] = hash_password(obj_data.pop("password"))
        obj_data["is_active"] = True
        db_obj = User(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class ItemCRUD(CRUDBase[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(Item)

    def get_by_upc(self, db: Session, upc: str) -> Item | None:
        return db.query(Item).filter(Item.upc == upc).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Item]:
        query = db.query(Item)
        if not include_inactive:
            query = query.filter(Item.is_active)
        return query.offset(skip).limit(limit).all()

    def create(
        self,
        db: Session,
        *,
        obj_in: ItemCreate,
        created_by_id: int = 1,
        upc_data: dict[str, Any] | None = None,
        uda_fetched: bool = False,
        uda_fetch_attempted: bool = False,
    ) -> Item:
        obj_data = obj_in.model_dump()
        obj_data["created_by"] = created_by_id
        obj_data["is_active"] = True
        obj_data["uda_fetched"] = uda_fetched
        obj_data["uda_fetch_attempted"] = uda_fetch_attempted
        obj_data["upc_data"] = upc_data if upc_data is not None else obj_data.get("upc_data")
        db_obj = Item(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def search(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> list[Item]:
        search_term = f"%{query}%"
        return (
            db.query(Item)
            .filter(
                and_(
                    Item.is_active,
                    or_(
                        Item.name.ilike(search_term),
                        Item.description.ilike(search_term),
                        Item.upc.like(search_term),
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )


class LocationCRUD(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def __init__(self):
        super().__init__(Location)

    def get_by_name(self, db: Session, name: str) -> Location | None:
        return db.query(Location).filter(Location.name == name).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Location]:
        query = db.query(Location)
        if not include_inactive:
            query = query.filter(Location.is_active)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: LocationCreate, created_by_id: int = 1) -> Location:
        obj_data = obj_in.model_dump()
        obj_data["created_by"] = created_by_id
        obj_data["is_active"] = True
        db_obj = Location(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def search(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> list[Location]:
        search_term = f"%{query}%"
        return (
            db.query(Location)
            .filter(
                and_(
                    Location.is_active,
                    or_(
                        Location.name.ilike(search_term),
                        Location.description.ilike(search_term),
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )


class SKUCRUD(CRUDBase[SKU, SKUCreate, SKUUpdate]):
    def __init__(self):
        super().__init__(SKU)

    def get_by_item(self, db: Session, item_id: int, skip: int = 0, limit: int = 100) -> list[SKU]:
        return (
            db.query(SKU)
            .filter(and_(SKU.item_id == item_id, SKU.is_active))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_location(
        self, db: Session, location_id: int, skip: int = 0, limit: int = 100
    ) -> list[SKU]:
        return (
            db.query(SKU)
            .filter(and_(SKU.location_id == location_id, SKU.is_active))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_item_location(self, db: Session, item_id: int, location_id: int) -> SKU | None:
        return (
            db.query(SKU)
            .filter(
                and_(
                    SKU.item_id == item_id,
                    SKU.location_id == location_id,
                    SKU.is_active,
                )
            )
            .first()
        )

    def get_low_stock(
        self, db: Session, skip: int = 0, limit: int = 100, threshold: float = 5.0
    ) -> list[SKU]:
        return (
            db.query(SKU)
            .filter(and_(SKU.is_active, SKU.quantity <= threshold))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[SKU]:
        query = db.query(SKU)
        if not include_inactive:
            query = query.filter(SKU.is_active)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: SKUCreate, created_by_id: int = 1) -> SKU:
        obj_data = obj_in.model_dump()
        obj_data["created_by"] = created_by_id
        obj_data["is_active"] = True
        db_obj = SKU(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def search(self, db: Session, query: str, skip: int = 0, limit: int = 50) -> list[SKU]:
        search_term = f"%{query}%"
        return (
            db.query(SKU)
            .join(Item)
            .join(Location)
            .filter(
                and_(
                    SKU.is_active,
                    or_(
                        Item.name.ilike(search_term),
                        Item.upc.like(search_term),
                        Location.name.ilike(search_term),
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_quantity(self, db: Session, sku_id: int, new_quantity: int) -> SKU | None:
        sku = db.query(SKU).filter(SKU.id == sku_id).first()
        if sku:
            sku.quantity = new_quantity
            db.commit()
            db.refresh(sku)
        return sku


class AlertCRUD(CRUDBase[Alert, AlertCreate, AlertUpdate]):
    def __init__(self):
        super().__init__(Alert)

    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> list[Alert]:
        return (
            db.query(Alert)
            .filter(and_(Alert.is_active, ~Alert.is_acknowledged))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Alert]:
        query = db.query(Alert)
        if not include_inactive:
            query = query.filter(Alert.is_active)
        return query.offset(skip).limit(limit).all()


class LogEntryCRUD(CRUDBase[LogEntry, None, None]):
    def __init__(self):
        super().__init__(LogEntry)

    def get_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[LogEntry]:
        return (
            db.query(LogEntry)
            .filter(LogEntry.user_id == user_id)
            .order_by(LogEntry.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_action(
        self, db: Session, action: str, skip: int = 0, limit: int = 100
    ) -> list[LogEntry]:
        return (
            db.query(LogEntry)
            .filter(LogEntry.action == action)
            .order_by(LogEntry.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


class ShoppingListCRUD(CRUDBase[ShoppingList, ShoppingListCreate, ShoppingListUpdate]):
    def __init__(self):
        super().__init__(ShoppingList)

    def get_accessible_lists(
        self,
        db: Session,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> tuple[list[ShoppingList], int]:
        """Get lists accessible to user (public + own private)"""
        query = db.query(ShoppingList).filter(
            or_(ShoppingList.is_public, ShoppingList.creator_id == current_user.id)
        )

        if not include_deleted:
            query = query.filter(~ShoppingList.is_deleted)

        total = query.count()
        lists = query.offset(skip).limit(limit).all()
        return lists, total

    def get_by_id_if_accessible(
        self, db: Session, list_id: int, current_user: User
    ) -> ShoppingList | None:
        """Get list if user has access (public or owner)"""
        return (
            db.query(ShoppingList)
            .filter(
                and_(
                    ShoppingList.id == list_id,
                    ~ShoppingList.is_deleted,
                    or_(
                        ShoppingList.is_public,
                        ShoppingList.creator_id == current_user.id,
                    ),
                )
            )
            .first()
        )

    def can_modify_list(self, shopping_list: ShoppingList, current_user: User) -> bool:
        """Check if user can modify the list (collaborative editing rules)"""
        # Public lists: anyone can modify
        # Private lists: only creator can modify
        if shopping_list.is_public:
            return True
        return shopping_list.creator_id == current_user.id

    def create(self, db: Session, obj_in: ShoppingListCreate, creator: User) -> ShoppingList:
        """Create new shopping list with logging"""
        obj_data = obj_in.model_dump()
        obj_data["creator_id"] = creator.id
        obj_data["is_deleted"] = False

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
            {"list_name": db_obj.name, "is_public": db_obj.is_public},
        )

        return db_obj

    def update(
        self,
        db: Session,
        db_obj: ShoppingList,
        obj_in: ShoppingListUpdate,
        current_user: User,
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
            self.log_action(db, db_obj, current_user, "updated", {"changes": changes})

        return db_obj

    def remove(self, db: Session, db_obj: ShoppingList, current_user: User) -> ShoppingList:
        """Soft delete shopping list with logging"""
        db_obj.is_deleted = True
        db.commit()
        db.refresh(db_obj)

        # Log the deletion
        self.log_action(db, db_obj, current_user, "deleted", {"list_name": db_obj.name})

        return db_obj

    def duplicate(
        self,
        db: Session,
        source_list: ShoppingList,
        duplicate_data: ShoppingListDuplicate,
        current_user: User,
    ) -> ShoppingList:
        """Duplicate shopping list with all items"""
        # Create new list
        new_list_data = {
            "name": duplicate_data.name,
            "is_public": duplicate_data.is_public,
            "creator_id": current_user.id,
            "is_deleted": False,
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
                    is_deleted=False,
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
                "new_list_name": new_list.name,
            },
        )

        return new_list

    def add_item(
        self,
        db: Session,
        shopping_list: ShoppingList,
        item_data: ShoppingListItemCreate,
        current_user: User,
    ) -> ShoppingListItem:
        """Add item to shopping list with logging"""
        # Check if item already exists in list (including soft-deleted)
        existing_item = (
            db.query(ShoppingListItem)
            .filter(
                and_(
                    ShoppingListItem.shopping_list_id == shopping_list.id,
                    ShoppingListItem.item_id == item_data.item_id,
                )
            )
            .first()
        )

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
                        "quantity": item_data.quantity,
                    },
                )

                return existing_item
            else:
                raise ValueError("Item already exists in shopping list")

        # Create new item
        obj_data = item_data.model_dump()
        obj_data["shopping_list_id"] = shopping_list.id
        obj_data["is_deleted"] = False

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
                "quantity": item_data.quantity,
            },
        )

        return db_obj

    def update_item_quantity(
        self,
        db: Session,
        list_item: ShoppingListItem,
        new_quantity: int,
        current_user: User,
    ) -> ShoppingListItem:
        """Update item quantity with logging"""
        old_quantity = list_item.quantity
        list_item.quantity = new_quantity
        db.commit()
        db.refresh(list_item)

        # Log the update
        item_obj = db.query(Item).filter(Item.id == list_item.item_id).first()
        shopping_list = (
            db.query(ShoppingList).filter(ShoppingList.id == list_item.shopping_list_id).first()
        )

        self.log_action(
            db,
            shopping_list,
            current_user,
            "item_updated",
            {
                "item_id": list_item.item_id,
                "item_name": item_obj.name if item_obj else "Unknown",
                "quantity": {"from": old_quantity, "to": new_quantity},
            },
        )

        return list_item

    def remove_item(self, db: Session, list_item: ShoppingListItem, current_user: User) -> None:
        """Remove item from shopping list with logging (soft delete)"""
        # Log before deletion
        item_obj = db.query(Item).filter(Item.id == list_item.item_id).first()
        shopping_list = (
            db.query(ShoppingList).filter(ShoppingList.id == list_item.shopping_list_id).first()
        )

        self.log_action(
            db,
            shopping_list,
            current_user,
            "item_removed",
            {
                "item_id": list_item.item_id,
                "item_name": item_obj.name if item_obj else "Unknown",
                "quantity": list_item.quantity,
            },
        )

        # Soft delete the item
        list_item.is_deleted = True
        db.commit()

    def get_list_item(
        self, db: Session, shopping_list_id: int, item_id: int
    ) -> ShoppingListItem | None:
        """Get a specific item from a shopping list"""
        return (
            db.query(ShoppingListItem)
            .filter(
                and_(
                    ShoppingListItem.shopping_list_id == shopping_list_id,
                    ShoppingListItem.item_id == item_id,
                    ~ShoppingListItem.is_deleted,
                )
            )
            .first()
        )

    def get_logs(
        self,
        db: Session,
        shopping_list_id: int,
        skip: int = 0,
        limit: int = 100,
        action_type: str | None = None,
    ) -> tuple[list[ShoppingListLog], int]:
        """Get logs for a shopping list"""
        query = (
            db.query(ShoppingListLog)
            .filter(ShoppingListLog.shopping_list_id == shopping_list_id)
            .order_by(ShoppingListLog.timestamp.desc())
        )

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
        details: dict[str, Any] | None = None,
    ) -> ShoppingListLog:
        """Log shopping list action"""
        import json

        log_entry = ShoppingListLog(
            shopping_list_id=shopping_list.id,
            user_id=user.id,
            action_type=action_type,
            details=json.dumps(details) if details else None,
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


class SessionCRUD:
    """CRUD operations for session-based authentication."""

    def __init__(self):
        self.model = SessionModel

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a session token with SHA-256 for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def create(self, db: Session, *, user_id: int, is_persistent: bool = False) -> str:
        """Create a new session. Returns the raw token (only shown once)."""
        import secrets

        raw_token = secrets.token_hex(32)  # 64-char hex string
        token_hash = self._hash_token(raw_token)

        expires_delta = (
            settings.PERSISTENT_SESSION_EXPIRE_DAYS
            if is_persistent
            else settings.SESSION_EXPIRE_HOURS / 24
        )
        from datetime import timedelta

        expires_at = datetime.now(UTC) + timedelta(days=expires_delta)

        session = SessionModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_persistent=is_persistent,
        )
        db.add(session)
        db.commit()
        return raw_token

    def get_user_by_token(self, db: Session, raw_token: str) -> User | None:
        """Look up a user by raw session token. Returns None if expired or not found."""
        token_hash = self._hash_token(raw_token)
        session = db.query(SessionModel).filter(SessionModel.token_hash == token_hash).first()
        if not session:
            return None
        # Compare with UTC, but handle SQLite's naive datetimes
        now = datetime.now(UTC)
        expires = session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < now:
            db.delete(session)
            db.commit()
            return None
        return db.query(User).filter(User.id == session.user_id).first()

    def delete(self, db: Session, raw_token: str) -> bool:
        """Delete a session by raw token. Returns True if found and deleted."""
        token_hash = self._hash_token(raw_token)
        session = db.query(SessionModel).filter(SessionModel.token_hash == token_hash).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    def delete_all_for_user(self, db: Session, user_id: int) -> int:
        """Delete all sessions for a user. Returns count deleted."""
        count = db.query(SessionModel).filter(SessionModel.user_id == user_id).delete()
        db.commit()
        return count

    def cleanup_expired(self, db: Session) -> int:
        """Delete all expired sessions. Returns count deleted."""
        now = datetime.now(UTC)
        # Handle SQLite naive datetimes by comparing with now.replace(tzinfo=None)
        sessions = db.query(SessionModel).all()
        count = 0
        for s in sessions:
            expires = s.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if expires < now:
                db.delete(s)
                count += 1
        db.commit()
        return count


session = SessionCRUD()
