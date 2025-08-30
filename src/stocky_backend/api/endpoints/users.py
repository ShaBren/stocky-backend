"""
User management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...models.models import User
from ...core.security import (
    get_current_active_user, 
    require_admin
)
from ...crud.crud import UserCRUD, LogEntryCRUD
from ...schemas.schemas import (
    UserCreate, 
    UserUpdate, 
    UserResponse
)

router = APIRouter()
user_crud = UserCRUD()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = user_crud.get_multi(db, skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users]


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    
    # Check if username already exists
    existing_user = user_crud.get_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_email = user_crud.get_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create user
    user = user_crud.create(db, obj_in=user_data)
    # Log creation
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"User created: {user.username} (ID: {user.id})",
        "level": "INFO",
        "module": "users",
        "function": "create_user",
        "user_id": current_user.id
    }
    log_crud.create(db, obj_in=log_entry)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID (admin or own profile)"""
    
    # Check if user can access this profile
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required or access own data only."
        )
    
    user = user_crud.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user (admin or own profile)"""
    
    # Check if user can update this profile
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required or access own data only."
        )
    
    # Only admins can change roles
    if user_update.role is not None and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user roles"
        )
    
    # Check if new username is taken (if being changed)
    if user_update.username is not None:
        existing_user = user_crud.get_by_username(db, user_update.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    # Check if new email is taken (if being changed)
    if user_update.email is not None:
        existing_email = user_crud.get_by_email(db, user_update.email)
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update user
    db_user = user_crud.get(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # Compare changes BEFORE update
    changes = {}
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(db_user, field, None)
        if value != old_value:
            changes[field] = {"old": old_value, "new": value}
    updated_user = user_crud.update(db, db_obj=db_user, obj_in=user_update)
    # Log update
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"User updated: {updated_user.username} (ID: {updated_user.id})",
        "level": "INFO",
        "module": "users",
        "function": "update_user",
        "user_id": current_user.id,
        "extra_data": {"changes": changes}
    }
    log_crud.create(db, obj_in=log_entry)
    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) user (admin only)"""
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = user_crud.get(db, user_id)
    user_crud.remove(db, id=user_id)
    # Log deletion
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"User deleted: {user.username} (ID: {user.id})",
        "level": "INFO",
        "module": "users",
        "function": "delete_user",
        "user_id": current_user.id
    }
    log_crud.create(db, obj_in=log_entry)
    return {"message": "User deactivated successfully"}
