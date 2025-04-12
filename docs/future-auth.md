# Future Authentication Implementation Guide

This document provides a blueprint for adding JWT-based authentication to protect the API endpoints in this project.

## 1. Authentication System Components

The authentication system consists of the following components:

1. **User Management**: Database and models for storing user credentials securely
2. **JWT Token System**: Token generation, validation, and refresh mechanisms
3. **Protected Routes**: Middleware to validate tokens for protected endpoints
4. **Admin Tools**: User creation, role management, etc.

## 2. Required Dependencies

These dependencies are already in your requirements.txt:

```
python-jose   # For JWT token handling
passlib       # Password hashing utilities
bcrypt        # Strong password hashing algorithm
```

## 3. Authentication Implementation

### 3.1 Create Security Module

Create a new file `app/core/security.py`:

```python
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)
```

### 3.2 Update Config Settings

Update `app/core/config.py` to include security settings:

```python
# Add these to the Settings class
SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
```

### 3.3 Create User Models

Create a new file `app/models/user.py`:

```python
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# User Schemas
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str
```

### 3.4 Create Database Models

Create models for database storage:

```python
# This example uses SQLAlchemy, but could be adapted for any ORM

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
```

### 3.5 Create Authentication Middleware

Create a new file `app/core/deps.py`:

```python
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import SessionLocal
from app.models.user import User
from app.crud.user import get_user_by_email

# Token URL is where clients should authenticate
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")

def get_db() -> Generator:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if the current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """Check if the current user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not enough permissions"
        )
    return current_user
```

### 3.6 Create Authentication Router

Create a new file `app/routers/auth.py`:

```python
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.crud.user import get_user_by_email, create_user, get_users
from app.models.token import Token

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = get_user_by_email(db, email=form_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.email, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/login/test-token", response_model=User)
def test_token(current_user: User = Depends(get_current_user)) -> Any:
    """Test access token."""
    return current_user
```

### 3.7 Create Token Schema

Create a new file `app/models/token.py`:

```python
from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
```

### 3.8 Add the Authentication Router to Main Application

Update `app/main.py`:

```python
# Add this import
from app.routers import auth

# Include the router
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
```

### 3.9 Protect API Endpoints

Update your existing routers to require authentication:

```python
# In app/routers/image_generation.py
from app.core.deps import get_current_active_user

@router.post(
    "/images/generate",
    response_model=ImageGenerationResponse,
    # ... existing code ...
)
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user),  # Add this line
    xai_client: XAIClient = Depends(get_xai_client)
) -> ImageGenerationResponse:
    # ... existing code ...
```

Repeat for other routers that need protection.

## 4. Database Setup

This implementation assumes a database backend for user storage. You'll need to set up:

1. Database connection in `app/db/session.py`
2. CRUD operations in `app/crud/user.py`
3. Database migrations for creating the users table

## 5. Environment Variables

Add these to your `.env` file:

```
SECRET_KEY=your-secret-key-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 6. Testing Authentication

### 6.1 Obtain a Token

```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin"
```

### 6.2 Use the Token

```bash
curl -X POST "http://localhost:8000/api/v1/images/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "prompt": "A beautiful mountain landscape with a lake in the foreground",
    "model": "grok-2-image"
  }'
```

## 7. Security Considerations

1. **Store Passwords Securely**: Always use bcrypt for password hashing, never store plaintext passwords
2. **Use HTTPS**: In production, always use HTTPS to protect tokens in transit
3. **Short Token Lifetimes**: Keep access token lifetimes short (30 mins or less)
4. **Strong Secret Key**: Use a strong, random SECRET_KEY at least 32 characters long
5. **Rate Limiting**: Implement rate limiting on login endpoints to prevent brute force attacks
6. **Audit Logging**: Log authentication events for security monitoring

## 8. Extending the Authentication System

This basic implementation can be extended with:

1. **Refresh Tokens**: For obtaining new access tokens without re-authentication
2. **Password Reset**: Email-based password reset functionality
3. **Role-Based Access Control**: More granular permissions system
4. **OAuth Integration**: Support for Google, GitHub, etc.
5. **API Keys**: Separate long-lived API keys for automated systems

## 9. User Administration

You'll likely want to add endpoints for:

1. User registration
2. User management (list, create, update, delete)
3. Role management
4. Self-service profile updates

This authentication system provides a solid foundation that can grow with your application's needs. 