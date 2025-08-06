"""
User management endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_users():
    """List all users"""
    return {"message": "Users list endpoint - to be implemented"}

@router.post("/")
async def create_user():
    """Create a new user"""
    return {"message": "User creation endpoint - to be implemented"}
