"""
Security dependencies for FastAPI authentication and authorization.
"""

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..core.auth import get_session_token_from_cookie
from ..crud.crud import session as session_crud
from ..db.database import get_db
from ..models.models import User, UserRole

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_session(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """Get current user from session cookie."""
    token = get_session_token_from_cookie(request)
    if not token:
        return None
    return session_crud.get_user_by_token(db, token)


async def get_current_user_from_api_key(
    db: Session = Depends(get_db),
    api_key: str | None = Security(api_key_header),
) -> User | None:
    """Get current user from API key header."""
    if not api_key:
        return None
    user = db.query(User).filter(User.api_key == api_key).first()
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    session_user: User | None = Depends(get_current_user_from_session),
    api_key_user: User | None = Depends(get_current_user_from_api_key),
) -> User:
    """Get current user from session cookie or API key."""
    user = session_user or api_key_user
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    return current_user


async def get_current_user_optional(
    session_user: User | None = Depends(get_current_user_from_session),
    api_key_user: User | None = Depends(get_current_user_from_api_key),
) -> User | None:
    """Get current user if authenticated, but don't require authentication."""
    user = session_user or api_key_user
    if user and not user.is_active:
        return None
    return user


def require_roles(allowed_roles: list[UserRole]):
    """Dependency factory to require specific user roles"""

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}",
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
        "admin": [UserRole.ADMIN],
    }

    allowed_roles = role_hierarchy.get(min_role, [UserRole.ADMIN])

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required minimum role: {min_role}",
            )
        return current_user

    return role_checker


# Convenience dependencies for common role combinations
require_admin = require_roles([UserRole.ADMIN])
require_member_or_admin = require_roles([UserRole.MEMBER, UserRole.ADMIN])
require_any_role = require_roles(
    [UserRole.ADMIN, UserRole.MEMBER, UserRole.SCANNER, UserRole.READ_ONLY]
)


def require_scanner_or_admin():
    """Allow scanners and admins"""
    return require_roles([UserRole.SCANNER, UserRole.ADMIN])


def require_write_access():
    """Require write access (Admin or Member)"""
    return require_roles([UserRole.ADMIN, UserRole.MEMBER])


def require_admin_or_self(user_id: int):
    """Require admin role or accessing own user data"""

    async def admin_or_self_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required or access own data only.",
            )
        return current_user

    return admin_or_self_checker
