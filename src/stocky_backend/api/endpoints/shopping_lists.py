"""
Shopping Lists management endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import json

from ...db.database import get_db
from ...crud.crud import shopping_list, item as item_crud
from ...schemas.schemas import (
    ShoppingListCreate, ShoppingListUpdate, ShoppingListDuplicate,
    ShoppingListResponse, ShoppingListSummary,
    ShoppingListItemCreate, ShoppingListItemUpdate, ShoppingListItemResponse,
    ShoppingListLogResponse,
    PaginatedShoppingListsResponse, PaginatedShoppingListLogsResponse
)
from ...core.security import get_current_active_user
from ...models.models import User

router = APIRouter()


@router.get("/", response_model=PaginatedShoppingListsResponse)
async def list_shopping_lists(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    include_deleted: bool = Query(False, description="Include deleted lists (admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List shopping lists accessible to the current user (public + own private)"""
    # Only admins can see deleted lists
    if include_deleted and current_user.role != "admin":
        include_deleted = False
    
    lists, total = shopping_list.get_accessible_lists(
        db, current_user, skip=skip, limit=limit, include_deleted=include_deleted
    )
    
    # Convert to summary format with item count
    summaries = []
    for shopping_list_obj in lists:
        # Count active items
        item_count = sum(1 for item in shopping_list_obj.items if not item.is_deleted)
        
        summary = ShoppingListSummary(
            id=shopping_list_obj.id,
            name=shopping_list_obj.name,
            is_public=shopping_list_obj.is_public,
            creator=shopping_list_obj.creator,
            item_count=item_count,
            created_at=shopping_list_obj.created_at,
            updated_at=shopping_list_obj.updated_at
        )
        summaries.append(summary)
    
    return PaginatedShoppingListsResponse(
        items=summaries,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{list_id}", response_model=ShoppingListResponse)
async def get_shopping_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get shopping list details with all items"""
    shopping_list_obj = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not shopping_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    # Get active items with full item details
    active_items = []
    for list_item in shopping_list_obj.items:
        if not list_item.is_deleted:
            item_response = ShoppingListItemResponse(
                id=list_item.id,
                item=list_item.item,
                quantity=list_item.quantity,
                created_at=list_item.created_at,
                updated_at=list_item.updated_at
            )
            active_items.append(item_response)
    
    return ShoppingListResponse(
        id=shopping_list_obj.id,
        name=shopping_list_obj.name,
        is_public=shopping_list_obj.is_public,
        creator=shopping_list_obj.creator,
        items=active_items,
        created_at=shopping_list_obj.created_at,
        updated_at=shopping_list_obj.updated_at
    )


@router.post("/", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def create_shopping_list(
    list_data: ShoppingListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new shopping list"""
    shopping_list_obj = shopping_list.create(db, list_data, current_user)
    
    return ShoppingListResponse(
        id=shopping_list_obj.id,
        name=shopping_list_obj.name,
        is_public=shopping_list_obj.is_public,
        creator=shopping_list_obj.creator,
        items=[],  # New list has no items
        created_at=shopping_list_obj.created_at,
        updated_at=shopping_list_obj.updated_at
    )


@router.put("/{list_id}", response_model=ShoppingListResponse)
async def update_shopping_list(
    list_id: int,
    list_data: ShoppingListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update shopping list metadata (name, visibility)"""
    shopping_list_obj = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not shopping_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    # Check if user can modify this list
    if not shopping_list.can_modify_list(shopping_list_obj, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this shopping list"
        )
    
    updated_list = shopping_list.update(db, shopping_list_obj, list_data, current_user)
    
    # Get active items for response
    active_items = []
    for list_item in updated_list.items:
        if not list_item.is_deleted:
            item_response = ShoppingListItemResponse(
                id=list_item.id,
                item=list_item.item,
                quantity=list_item.quantity,
                created_at=list_item.created_at,
                updated_at=list_item.updated_at
            )
            active_items.append(item_response)
    
    return ShoppingListResponse(
        id=updated_list.id,
        name=updated_list.name,
        is_public=updated_list.is_public,
        creator=updated_list.creator,
        items=active_items,
        created_at=updated_list.created_at,
        updated_at=updated_list.updated_at
    )


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete (soft delete) a shopping list"""
    shopping_list_obj = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not shopping_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    # Check if user can modify this list
    if not shopping_list.can_modify_list(shopping_list_obj, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this shopping list"
        )
    
    shopping_list.remove(db, shopping_list_obj, current_user)
    return None


@router.post("/{list_id}/duplicate", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_shopping_list(
    list_id: int,
    duplicate_data: ShoppingListDuplicate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Duplicate a shopping list with all its items"""
    source_list = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not source_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    duplicated_list = shopping_list.duplicate(db, source_list, duplicate_data, current_user)
    
    # Get items for response
    active_items = []
    for list_item in duplicated_list.items:
        if not list_item.is_deleted:
            item_response = ShoppingListItemResponse(
                id=list_item.id,
                item=list_item.item,
                quantity=list_item.quantity,
                created_at=list_item.created_at,
                updated_at=list_item.updated_at
            )
            active_items.append(item_response)
    
    return ShoppingListResponse(
        id=duplicated_list.id,
        name=duplicated_list.name,
        is_public=duplicated_list.is_public,
        creator=duplicated_list.creator,
        items=active_items,
        created_at=duplicated_list.created_at,
        updated_at=duplicated_list.updated_at
    )


@router.post("/{list_id}/items", response_model=ShoppingListItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_shopping_list(
    list_id: int,
    item_data: ShoppingListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add an item to a shopping list"""
    shopping_list_obj = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not shopping_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    # Check if user can modify this list
    if not shopping_list.can_modify_list(shopping_list_obj, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this shopping list"
        )
    
    # Verify that the item exists
    item_obj = item_crud.get(db, item_data.item_id)
    if not item_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    try:
        list_item = shopping_list.add_item(db, shopping_list_obj, item_data, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    return ShoppingListItemResponse(
        id=list_item.id,
        item=list_item.item,
        quantity=list_item.quantity,
        created_at=list_item.created_at,
        updated_at=list_item.updated_at
    )


@router.put("/{list_id}/items/{item_id}", response_model=ShoppingListItemResponse)
async def update_item_in_shopping_list(
    list_id: int,
    item_id: int,
    quantity_data: ShoppingListItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update the quantity of an item in a shopping list"""
    shopping_list_obj = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not shopping_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    # Check if user can modify this list
    if not shopping_list.can_modify_list(shopping_list_obj, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this shopping list"
        )
    
    # Get the list item
    list_item = shopping_list.get_list_item(db, list_id, item_id)
    if not list_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in shopping list"
        )
    
    updated_item = shopping_list.update_item_quantity(
        db, list_item, quantity_data.quantity, current_user
    )
    
    return ShoppingListItemResponse(
        id=updated_item.id,
        item=updated_item.item,
        quantity=updated_item.quantity,
        created_at=updated_item.created_at,
        updated_at=updated_item.updated_at
    )


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_shopping_list(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove an item from a shopping list"""
    shopping_list_obj = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not shopping_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    # Check if user can modify this list
    if not shopping_list.can_modify_list(shopping_list_obj, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this shopping list"
        )
    
    # Get the list item
    list_item = shopping_list.get_list_item(db, list_id, item_id)
    if not list_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in shopping list"
        )
    
    shopping_list.remove_item(db, list_item, current_user)
    return None


@router.get("/{list_id}/logs", response_model=PaginatedShoppingListLogsResponse)
async def get_shopping_list_logs(
    list_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get logs for a shopping list (available to any user who can view the list)"""
    shopping_list_obj = shopping_list.get_by_id_if_accessible(db, list_id, current_user)
    if not shopping_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shopping list not found or access denied"
        )
    
    logs, total = shopping_list.get_logs(
        db, list_id, skip=skip, limit=limit, action_type=action_type
    )
    
    # Convert logs to response format
    log_responses = []
    for log in logs:
        details = None
        if log.details:
            try:
                details = json.loads(log.details)
            except json.JSONDecodeError:
                details = {"raw": log.details}
        
        log_response = ShoppingListLogResponse(
            id=log.id,
            action_type=log.action_type,
            user=log.user,
            details=details,
            timestamp=log.timestamp
        )
        log_responses.append(log_response)
    
    return PaginatedShoppingListLogsResponse(
        items=log_responses,
        total=total,
        skip=skip,
        limit=limit
    )