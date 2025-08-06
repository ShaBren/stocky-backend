"""
Scanner interaction endpoints
"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/scan")
async def scanner_scan():
    """Handle barcode scan from scanner"""
    return {"message": "Scanner scan endpoint - to be implemented"}

@router.get("/status")
async def scanner_status():
    """Get scanner status"""
    return {"message": "Scanner status endpoint - to be implemented"}

@router.post("/associate")
async def associate_scanner():
    """Associate scanner with UI instance"""
    return {"message": "Scanner association endpoint - to be implemented"}
