# app/services/auth_service.py
import jwt
import secrets
import hashlib
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.models import User, UserCreate, UserLogin, AuthResponse, APIKey, APIKeyCreate, APIKeyResponse
from app.config import DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
    
    @staticmethod
    async def initialize_db():
        """Initialize the authentication database tables."""
        async with aiosqlite.connect(DATABASE_URL) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # API keys table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            await db.commit()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except jwt.PyJWTError:
            return None
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        async with aiosqlite.connect(DATABASE_URL) as db:
            # Check if user already exists
            cursor = await db.execute(
                "SELECT id FROM users WHERE email = ? OR username = ?",
                (user_data.email, user_data.username)
            )
            existing_user = await cursor.fetchone()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email or username already exists"
                )
            
            # Create new user
            user_id = secrets.token_urlsafe(32)
            password_hash = self.get_password_hash(user_data.password)
            
            await db.execute("""
                INSERT INTO users (id, email, username, password_hash)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_data.email, user_data.username, password_hash))
            
            await db.commit()
            
            # Return created user
            cursor = await db.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            user_row = await cursor.fetchone()
            
            return User(
                id=user_row[0],
                email=user_row[1],
                username=user_row[2],
                is_active=bool(user_row[4]),
                created_at=datetime.fromisoformat(user_row[5]),
                updated_at=datetime.fromisoformat(user_row[6])
            )
    
    async def authenticate_user(self, user_data: UserLogin) -> Optional[User]:
        """Authenticate a user with email and password."""
        async with aiosqlite.connect(DATABASE_URL) as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE email = ?",
                (user_data.email,)
            )
            user_row = await cursor.fetchone()
            
            if not user_row:
                return None
            
            if not self.verify_password(user_data.password, user_row[3]):
                return None
            
            return User(
                id=user_row[0],
                email=user_row[1],
                username=user_row[2],
                is_active=bool(user_row[4]),
                created_at=datetime.fromisoformat(user_row[5]),
                updated_at=datetime.fromisoformat(user_row[6])
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        async with aiosqlite.connect(DATABASE_URL) as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            user_row = await cursor.fetchone()
            
            if not user_row:
                return None
            
            return User(
                id=user_row[0],
                email=user_row[1],
                username=user_row[2],
                is_active=bool(user_row[4]),
                created_at=datetime.fromisoformat(user_row[5]),
                updated_at=datetime.fromisoformat(user_row[6])
            )
    
    async def create_api_key(self, user_id: str, key_data: APIKeyCreate) -> APIKeyResponse:
        """Create a new API key for a user."""
        async with aiosqlite.connect(DATABASE_URL) as db:
            # Generate API key
            api_key = f"gemini_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            key_id = secrets.token_urlsafe(16)
            
            await db.execute("""
                INSERT INTO api_keys (id, user_id, name, key_hash)
                VALUES (?, ?, ?, ?)
            """, (key_id, user_id, key_data.name, key_hash))
            
            await db.commit()
            
            return APIKeyResponse(
                id=key_id,
                name=key_data.name,
                key=api_key,  # Only shown once
                is_active=True,
                created_at=datetime.utcnow(),
                last_used=None
            )
    
    async def get_user_api_keys(self, user_id: str) -> List[APIKeyResponse]:
        """Get all API keys for a user."""
        async with aiosqlite.connect(DATABASE_URL) as db:
            cursor = await db.execute("""
                SELECT id, name, is_active, created_at, last_used
                FROM api_keys 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            rows = await cursor.fetchall()
            
            return [
                APIKeyResponse(
                    id=row[0],
                    name=row[1],
                    key="***",  # Don't show the actual key
                    is_active=bool(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    last_used=datetime.fromisoformat(row[4]) if row[4] else None
                )
                for row in rows
            ]
    
    async def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify an API key and return the user ID."""
        print(f"DEBUG: Verifying API key: {api_key[:10]}...")
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        print(f"DEBUG: Key hash: {key_hash[:10]}...")
        
        async with aiosqlite.connect(DATABASE_URL) as db:
            cursor = await db.execute("""
                SELECT user_id FROM api_keys 
                WHERE key_hash = ? AND is_active = TRUE
            """, (key_hash,))
            
            row = await cursor.fetchone()
            print(f"DEBUG: Database query result: {row}")
            
            if not row:
                print("DEBUG: No matching API key found in database")
                return None
            
            # Update last_used
            await db.execute("""
                UPDATE api_keys SET last_used = CURRENT_TIMESTAMP
                WHERE key_hash = ?
            """, (key_hash,))
            
            await db.commit()
            
            print(f"DEBUG: API key verified for user: {row[0]}")
            return row[0]
    
    async def delete_api_key(self, user_id: str, key_id: str) -> bool:
        """Delete an API key."""
        async with aiosqlite.connect(DATABASE_URL) as db:
            cursor = await db.execute("""
                DELETE FROM api_keys 
                WHERE id = ? AND user_id = ?
            """, (key_id, user_id))
            
            await db.commit()
            return cursor.rowcount > 0