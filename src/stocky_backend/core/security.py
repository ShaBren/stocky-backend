"""
Security dependencies for FastAPI authentication and authorization
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.models import User, UserRole
from ..core.auth import verify_token_payload


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_token(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Optional[User]:
    """Get current user from JWT token"""
    if not credentials:
        return None
    
    # Verify the token
    payload = verify_token_payload(credentials.credentials)
    
    # Extract user data
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_from_api_key(
    db: Session = Depends(get_db),
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[User]:
    """Get current user from API key"""
    if not api_key:
        return None
    
    # Get user from database by API key
    user = db.query(User).filter(User.api_key == api_key).first()
    if user is None or not user.is_active:
        return None
    
    return user


async def get_current_user(
    token_user: Optional[User] = Depends(get_current_user_from_token),
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key)
) -> User:
    """Get current user from either JWT token or API key"""
    user = token_user or api_key_user
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (already checked in get_current_user)"""
    return current_user


async def get_current_user_optional(
    token_user: Optional[User] = Depends(get_current_user_from_token),
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key)
) -> Optional[User]:
    """Get current user if authenticated, but don't require authentication"""
    return token_user or api_key_user


def require_roles(allowed_roles: List[UserRole]):
    """Dependency factory to require specific user roles"""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


def require_user_role(min_role: str = "user"):
    """Dependency factory to require minimum user role"""
    role_hierarchy = {
        "user": [UserRole.ADMIN, UserRole.MEMBER, UserRole.SCANNER, UserRole.READ_ONLY],
        "scanner": [UserRole.ADMIN, UserRole.MEMBER, UserRole.SCANNER],
        "member": [UserRole.ADMIN, UserRole.MEMBER],
        "manager": [UserRole.ADMIN, UserRole.MEMBER],  # Member is essentially manager
        "admin": [UserRole.ADMIN]
    }
    
    allowed_roles = role_hierarchy.get(min_role, [UserRole.ADMIN])
    
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required minimum role: {min_role}"
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common role combinations
require_admin = require_roles([UserRole.ADMIN])
require_member_or_admin = require_roles([UserRole.MEMBER, UserRole.ADMIN])
require_any_role = require_roles([UserRole.ADMIN, UserRole.MEMBER, UserRole.SCANNER, UserRole.READ_ONLY])


def require_scanner_or_admin():
    """Allow scanners and admins"""
    return require_roles([UserRole.SCANNER, UserRole.ADMIN])


def require_write_access():
    """Require write access (Admin or Member)"""
    return require_roles([UserRole.ADMIN, UserRole.MEMBER])


def require_admin_or_self(user_id: int):
    """Require admin role or accessing own user data"""
    async def admin_or_self_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required or access own data only."
            )
        return current_user
    
    return admin_or_self_checker
