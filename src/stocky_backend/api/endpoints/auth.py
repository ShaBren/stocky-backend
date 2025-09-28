
"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...models.models import User
from ...core.auth import (
    verify_password, create_token_response, generate_api_key,
    create_persistent_token_response, set_refresh_token_cookie, clear_refresh_token_cookie,
    get_refresh_token_from_cookie, verify_token_payload
)
from ...core.security import get_current_active_user
from ...schemas.schemas import Token, LoginRequest, UserResponse

router = APIRouter()

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token using a valid refresh token from header or cookie"""
    # Check if there's a refresh token in cookies (for persistent sessions)
    cookie_refresh_token = get_refresh_token_from_cookie(request)
    is_persistent_session = cookie_refresh_token is not None
    
    # Generate new tokens for the authenticated user
    token_response = create_persistent_token_response(
        current_user.id, current_user.username, current_user.role, 
        remember_me=is_persistent_session
    )
    
    # If this was a cookie-based session, update the cookie with the new refresh token
    if is_persistent_session:
        set_refresh_token_cookie(
            response, 
            token_response["refresh_token"], 
            persistent=True
        )
    
    return Token(**token_response)


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = False,
    db: Session = Depends(get_db)
):
    """User login with username/password to get JWT token
    
    Form fields:
    - username: User's username
    - password: User's password  
    - remember_me: Optional boolean for persistent session (default: false)
    """
    
    # Get user from database
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token response with persistent session support
    token_response = create_persistent_token_response(
        user.id, user.username, user.role, remember_me=remember_me
    )
    
    # Set refresh token in cookie if remember_me is enabled
    if remember_me:
        set_refresh_token_cookie(
            response, 
            token_response["refresh_token"], 
            persistent=True
        )
    
    return Token(**token_response)


@router.post("/login-json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """User login with JSON payload to get JWT token"""
    
    # Get user from database
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Create token response with persistent session support
    token_response = create_persistent_token_response(
        user.id, user.username, user.role, remember_me=login_data.remember_me
    )
    
    # Set refresh token in cookie if remember_me is enabled
    if login_data.remember_me:
        set_refresh_token_cookie(
            response, 
            token_response["refresh_token"], 
            persistent=True
        )
    
    return Token(**token_response)


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """User logout endpoint (clears cookies and client should discard tokens)"""
    # Clear refresh token cookie if it exists
    clear_refresh_token_cookie(response)
    
    return {"message": f"User {current_user.username} logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.post("/generate-api-key")
async def generate_new_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for the current user"""
    
    # Generate new API key
    new_api_key = generate_api_key()
    
    # Update user with new API key
    current_user.api_key = new_api_key
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "API key generated successfully",
        "api_key": new_api_key,
        "note": "Store this API key securely. It will not be shown again."
    }


@router.delete("/revoke-api-key")
async def revoke_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke the current user's API key"""
    
    # Remove API key
    current_user.api_key = None
    db.commit()
    
    return {"message": "API key revoked successfully"}
