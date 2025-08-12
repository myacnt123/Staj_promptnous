# my_fastapi_angular_backend_v2/app/schemas/prompt.py

from pydantic import BaseModel, Field # Import Field for optional default values
from typing import Optional # For optional fields
from datetime import datetime # For datetime fields in responses

# --- Base Schema for Prompt properties common to creation and public view ---
class PromptBase(BaseModel):
    content: str = Field(..., min_length=1) # Prompt content, required
    is_public: bool = True # Default to public, can be set to false by user

# --- Schema for creating a new Prompt (input for POST /prompts/) ---
class PromptCreate(PromptBase):
    pass # Inherits all fields from PromptBase, no extra fields needed for creation


class PromptPure(BaseModel):
    content: str = Field(..., min_length=1)
# --- Schema for a public view of a Prompt (output for GET /prompts/ or similar) ---
class PromptPublic(PromptBase):
    id: int # Include the database ID
    user_id: int # ID of the author
    author_username: Optional[str] = None # Will be populated via relationship, not direct DB column
    no_of_likes: int = 0 # Will be populated by a query or ORM relationship, not direct DB column
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        # Pydantic v2: use from_attributes = True (replaces orm_mode = True)
        from_attributes = True

class PromptWithLikeStatus(PromptPublic):
    is_liked_by_user: bool = False
    class Config:
        from_attributes = True

# --- Schema for liking/unliking a Prompt (input for POST /prompts/{prompt_id}/like) ---
class PromptLikeCreate(BaseModel):
    # This schema is simple, usually just takes prompt_id from path
    # But it could be expanded if you had other like properties (e.g., 'rating')
    pass

# --- Schema for a single PromptLike entry (used internally or for debugging) ---
class PromptLikePublic(BaseModel):
    id: int
    prompt_id: int
    user_id: int

    class Config:
        from_attributes = True

