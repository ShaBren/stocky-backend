
"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...models.models import User
from ...core.auth import verify_password, create_token_response, generate_api_key
from ...core.security import get_current_active_user
from ...schemas.schemas import Token, LoginRequest, UserResponse

router = APIRouter()

@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token using a valid refresh token"""
    # The refresh token comes from the Authorization header via get_current_active_user
    # This ensures the refresh token is valid and the user is active
    
    # Generate new tokens for the authenticated user
    token_response = create_token_response(current_user.id, current_user.username, current_user.role)
    return Token(**token_response)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login with username/password to get JWT token"""
    
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
    
    # Create and return token
    token_response = create_token_response(user.id, user.username, user.role)
    return Token(**token_response)


@router.post("/login-json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
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
    
    # Create and return token
    token_response = create_token_response(user.id, user.username, user.role)
    return Token(**token_response)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """User logout endpoint (client should discard token)"""
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


# Trailing slash versions to avoid HTTPS redirect issues
# These call the same functions but with trailing slashes to match frontend expectations

@router.post("/refresh/", response_model=Token, include_in_schema=False)
async def refresh_token_trailing_slash(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token using a valid refresh token (trailing slash version)"""
    return await refresh_token(db, current_user)


@router.post("/login/", response_model=Token, include_in_schema=False)
async def login_trailing_slash(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login with username/password to get JWT token (trailing slash version)"""
    return await login(form_data, db)


@router.post("/login-json/", response_model=Token, include_in_schema=False)
async def login_json_trailing_slash(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
):
    """User login with JSON request body to get JWT token (trailing slash version)"""
    return await login_json(login_request, db)


@router.post("/logout/", include_in_schema=False)
async def logout_trailing_slash(
    current_user: User = Depends(get_current_active_user)
):
    """User logout (trailing slash version)"""
    return await logout(current_user)


@router.post("/generate-api-key/", include_in_schema=False)
async def generate_user_api_key_trailing_slash(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for the current user (trailing slash version)"""
    return await generate_new_api_key(current_user, db)


@router.delete("/revoke-api-key/", include_in_schema=False)
async def revoke_api_key_trailing_slash(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke the current user's API key (trailing slash version)"""
    return await revoke_api_key(current_user, db)


@router.get("/me/", response_model=UserResponse, include_in_schema=False)
async def get_current_user_info_trailing_slash(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information (trailing slash version)"""
    return await get_current_user_info(current_user)
