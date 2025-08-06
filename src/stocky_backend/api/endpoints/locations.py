"""
Location management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.crud import LocationCRUD
from ...schemas.schemas import LocationCreate, LocationUpdate, LocationResponse
from ...core.security import require_user_role

router = APIRouter()
location_crud = LocationCRUD()

@router.get("/", response_model=List[LocationResponse])
async def list_locations(
    skip: int = Query(0, ge=0, description="Number of locations to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of locations to return"),
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """List all locations with pagination"""
    locations = location_crud.get_multi(db, skip=skip, limit=limit)
    return locations

@router.post("/", response_model=LocationResponse)
async def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("manager"))
):
    """Create a new location"""
    # Check if location with same name already exists
    existing_location = location_crud.get_by_name(db, name=location.name)
    if existing_location:
        raise HTTPException(
            status_code=400,
            detail=f"Location with name '{location.name}' already exists"
        )
    
    db_location = location_crud.create(db, obj_in=location, created_by_id=current_user.id)
    return db_location

@router.get("/search", response_model=List[LocationResponse])
async def search_locations(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of locations to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of locations to return"),
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Search locations by name or description"""
    locations = location_crud.search(db, query=q, skip=skip, limit=limit)
    return locations

@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Get a specific location by ID"""
    location = location_crud.get(db, id=location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    location_update: LocationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("manager"))
):
    """Update an existing location"""
    db_location = location_crud.get(db, id=location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if updating name would conflict with existing location
    if location_update.name and location_update.name != db_location.name:
        existing_location = location_crud.get_by_name(db, name=location_update.name)
        if existing_location and existing_location.id != location_id:
            raise HTTPException(
                status_code=400,
                detail=f"Location with name '{location_update.name}' already exists"
            )
    
    updated_location = location_crud.update(db, db_obj=db_location, obj_in=location_update)
    return updated_location

@router.delete("/{location_id}")
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("admin"))
):
    """Delete a location (admin only)"""
    db_location = location_crud.get(db, id=location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # TODO: Check if location has any items before deleting
    location_crud.remove(db, id=location_id)
    return {"message": "Location deleted successfully"}

@router.get("/name/{name}", response_model=LocationResponse)
async def get_location_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Get a location by name"""
    location = location_crud.get_by_name(db, name=name)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location
