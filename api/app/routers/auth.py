# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Union
from datetime import timedelta

from app.models import (
    UserCreate, UserLogin, AuthResponse, User,
    APIKeyCreate, APIKeyResponse, APIKeyList
)
from app.services.auth_service import AuthService
from app.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

@router.get("/test", response_model=dict)
async def test_endpoint():
    """Test endpoint to verify router is working."""
    return {"message": "Auth router is working"}

@router.get("/debug", response_model=dict)
async def debug_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None),
):
    """Debug endpoint to check authentication headers."""
    return {
        "credentials": str(credentials),
        "x_api_key": x_api_key[:10] + "..." if x_api_key else None,
        "headers_received": True
    }

# Dependency to get auth service
def get_auth_service() -> AuthService:
    return AuthService()

# Dependency to get current user from JWT token
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = auth_service.verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

# Dependency to get current user from API key
async def get_current_user_from_api_key(
    x_api_key: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    user_id = await auth_service.verify_api_key(x_api_key)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

# Dependency that tries JWT first, then API key
async def get_current_user_any(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    print(f"DEBUG: get_current_user_any called")
    print(f"DEBUG: credentials: {credentials}")
    print(f"DEBUG: x_api_key: {x_api_key[:10] if x_api_key else None}...")
    
    # Try JWT first
    if credentials:
        try:
            print(f"DEBUG: Trying JWT authentication")
            user_id = auth_service.verify_token(credentials.credentials)
            if user_id:
                user = await auth_service.get_user_by_id(user_id)
                if user and user.is_active:
                    print(f"DEBUG: JWT authentication successful for user: {user.username}")
                    return user
        except Exception as e:
            print(f"DEBUG: JWT authentication failed: {e}")
    
    # Try API key
    if x_api_key:
        try:
            print(f"DEBUG: Trying API key authentication")
            user_id = await auth_service.verify_api_key(x_api_key)
            if user_id:
                user = await auth_service.get_user_by_id(user_id)
                if user and user.is_active:
                    print(f"DEBUG: API key authentication successful for user: {user.username}")
                    return user
        except Exception as e:
            print(f"DEBUG: API key authentication failed: {e}")
    
    print(f"DEBUG: All authentication methods failed")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )

@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        user = await auth_service.create_user(user_data)
        
        # Create access token
        access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        return AuthResponse(
            access_token=access_token,
            user=user,
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=AuthResponse)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login with email and password."""
    user = await auth_service.authenticate_user(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        user=user,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_any)
):
    """Get current user information (supports both JWT and API key authentication)."""
    return current_user

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a new API key for the current user."""
    return await auth_service.create_api_key(current_user.id, key_data)

@router.get("/api-keys", response_model=APIKeyList)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """List all API keys for the current user."""
    keys = await auth_service.get_user_api_keys(current_user.id)
    return APIKeyList(keys=keys)

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Delete an API key."""
    success = await auth_service.delete_api_key(current_user.id, key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key deleted successfully"}

@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"message": "Successfully logged out"}