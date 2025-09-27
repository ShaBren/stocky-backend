"""
Main API router that includes all endpoint modules
"""
from fastapi import APIRouter

from .endpoints import auth, users, items, locations, skus, scanner, logs, alerts, backup, shopping_lists

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(skus.router, prefix="/skus", tags=["inventory"])
api_router.include_router(scanner.router, prefix="/scanner", tags=["scanner"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(backup.router, prefix="/backup", tags=["backup"])
api_router.include_router(shopping_lists.router, prefix="/shopping-lists", tags=["shopping-lists"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stocky-backend"}
