"""
Authentication endpoints — session-based auth.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.auth import (
    clear_session_cookie,
    generate_api_key,
    get_session_token_from_cookie,
    hash_password,
    set_session_cookie,
    verify_password,
)
from ...core.security import get_current_active_user
from ...crud.crud import session as session_crud
from ...db.database import get_db
from ...models.models import User
from ...schemas.schemas import LoginRequest, PasswordChange, SessionResponse, UserResponse

router = APIRouter()


@router.post("/login", response_model=SessionResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = False,
    db: Session = Depends(get_db),
):
    """User login — creates a session, sets cookie, returns user info."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    raw_token = session_crud.create(db, user_id=user.id, is_persistent=remember_me)
    set_session_cookie(response, raw_token, persistent=remember_me)
    return SessionResponse(user_id=user.id, role=user.role, username=user.username)


@router.post("/login-json", response_model=SessionResponse)
async def login_json(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """User login via JSON — creates a session, sets cookie, returns user info."""
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    raw_token = session_crud.create(db, user_id=user.id, is_persistent=login_data.remember_me)
    set_session_cookie(response, raw_token, persistent=login_data.remember_me)
    return SessionResponse(user_id=user.id, role=user.role, username=user.username)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """User logout — deletes session from DB and clears cookie."""
    token = get_session_token_from_cookie(request)
    if token:
        session_crud.delete(db, token)
    clear_session_cookie(response)
    return {"message": f"User {current_user.username} logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from current password",
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/generate-api-key")
async def generate_new_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a new API key for the current user."""
    new_api_key = generate_api_key()
    current_user.api_key = new_api_key
    db.commit()
    db.refresh(current_user)
    return {
        "message": "API key generated successfully",
        "api_key": new_api_key,
        "note": "Store this API key securely. It will not be shown again.",
    }


@router.delete("/revoke-api-key")
async def revoke_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke the current user's API key."""
    current_user.api_key = None
    db.commit()
    return {"message": "API key revoked successfully"}
