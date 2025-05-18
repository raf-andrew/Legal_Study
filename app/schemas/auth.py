from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema."""
    username: constr(min_length=3, max_length=64)
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    """Schema for user creation."""
    password: constr(min_length=8)
    password_confirm: str

    def validate_passwords_match(self):
        """Validate that passwords match."""
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return True

class UserUpdate(BaseModel):
    """Schema for user update."""
    username: Optional[constr(min_length=3, max_length=64)] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Schema for token payload."""
    sub: str
    exp: datetime
    type: str = "access"

class TokenPayload(BaseModel):
    """Schema for token data."""
    sub: Optional[int] = None 