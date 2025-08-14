# my_fastapi_angular_backend/app/schemas/user.py
from datetime import datetime

from pydantic import BaseModel, EmailStr
from typing import Optional

# Base schema for common user attributes
class UserBase(BaseModel):
    username: str # Added for consistency with authentication logic
    first_name: str
    last_name: str
    email: EmailStr # Pydantic validates this as a valid email format

# Schema for creating a new user (input from registration form)
class UserCreate(UserBase):
    password: str # This is the plain-text password provided by the user

# Schema for updating a user (all fields are optional)
class UserUpdate(UserBase):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None # Example: for an admin to activate/deactivate a user

# Schema for internal use / when you need the hashed password (e.g., in CRUD operations or authentication logic)
class UserInDB(UserBase):
    id: int # This will be the database-generated ID
    hashed_password: str # This is where the hashed password lives
    is_active: bool
    totp_enabled: bool = False
    totp_secret: Optional[str] = None

    class Config:
        # Important for Pydantic V2 to work with ORM models.
        # It allows Pydantic models to be created from SQLAlchemy ORM objects.
        from_attributes = True

# Schema for returning public user data (NEVER include hashed_password or plain password)
class UserPublic(UserBase):
    id: int # This will be the database-generated ID
    is_active: bool # Whether the user account is active

    class Config:
        from_attributes = True
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str

class UserDelete(BaseModel):
        current_password: Optional[str] = None
        user_id: int
