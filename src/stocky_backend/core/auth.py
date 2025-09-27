"""
Authentication utilities for JWT tokens and password hashing
"""
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Union, TYPE_CHECKING
import secrets
import string

from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings

if TYPE_CHECKING:
    from ..models.models import User, UserRole


# Password hashing context
# Use direct bcrypt to avoid passlib compatibility issues with Python 3.13
import bcrypt as _bcrypt

class BcryptContext:
    """Direct bcrypt wrapper to avoid passlib compatibility issues"""
    
    @staticmethod
    def hash(password: str) -> str:
        """Hash a password using bcrypt"""
        # Encode password and ensure it's not longer than 72 bytes
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Generate salt and hash
        salt = _bcrypt.gensalt(rounds=12)
        hashed_bytes = _bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode('utf-8')
    
    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Encode password and ensure it's not longer than 72 bytes
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            
            # Verify password
            hashed_bytes = hashed.encode('utf-8')
            return _bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

pwd_context = BcryptContext()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


# Alias for compatibility
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token_payload(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_token_response(user_id: int, username: str, role: "UserRole") -> Dict[str, Any]:
    """Create a complete token response"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=7)

    token_data = {
        "sub": str(user_id),
        "username": username,
        "role": role,
    }

    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )

    refresh_token = create_access_token(
        data={"sub": str(user_id), "type": "refresh"},
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        "user_id": user_id,
        "role": role,
        "refresh_token": refresh_token,
    }


def authenticate_user(db: Session, username: str, password: str) -> Union[bool, "User"]:
    """Authenticate a user with username and password."""
    from ..crud import crud
    
    user = crud.user.get_by_username(db, username=username)
    if not user:
        return False
    if not user.is_active:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(db: Session, token: str) -> "User":
    """Get current user from JWT token."""
    from ..crud import crud
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token_payload(token)
        
        # Try to get user by ID first (preferred method)
        user_id = payload.get("sub")
        if user_id:
            try:
                user = crud.user.get(db, id=int(user_id))
                if user:
                    if not user.is_active:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Inactive user"
                        )
                    return user
            except (ValueError, TypeError):
                pass
        
        # Fall back to username lookup
        username: str = payload.get("username")
        if username:
            user = crud.user.get_by_username(db, username=username)
            if user:
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Inactive user"
                    )
                return user
        
        raise credentials_exception
        
    except JWTError:
        raise credentials_exception


def verify_token_simple(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# Create an alias for the tests that expect this name
def verify_token(token: str, db: Session = None) -> Optional["User"]:
    """Verify token and return user (for test compatibility)."""
    if db is None:
        # If no db session provided, just verify token
        payload = verify_token_simple(token)
        return payload
    
    # With db session, return actual user
    from ..crud import crud
    
    payload = verify_token_simple(token)
    if not payload:
        return None
    
    # Try to get user by ID first (preferred method)
    user_id = payload.get("sub")
    if user_id:
        try:
            user = crud.user.get(db, id=int(user_id))
            if user:
                return user
        except (ValueError, TypeError):
            pass
    
    # Fall back to username lookup
    username = payload.get("username")
    if username:
        user = crud.user.get_by_username(db, username=username)
        return user
    
    return None
