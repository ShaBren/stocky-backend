"""
SKU (inventory) management endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_skus():
    """List all SKUs (inventory items)"""
    return {"message": "SKUs list endpoint - to be implemented"}

@router.post("/")
async def create_sku():
    """Create a new SKU"""
    return {"message": "SKU creation endpoint - to be implemented"}

@router.put("/{sku_id}/quantity")
async def update_quantity():
    """Update SKU quantity"""
    return {"message": "SKU quantity update endpoint - to be implemented"}
