"""
Location management endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_locations():
    """List all locations"""
    return {"message": "Locations list endpoint - to be implemented"}

@router.post("/")
async def create_location():
    """Create a new location"""
    return {"message": "Location creation endpoint - to be implemented"}
