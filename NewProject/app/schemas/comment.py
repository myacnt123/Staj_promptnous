# my_fastapi_angular_backend_v2/app/schemas/comment.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Base schema for common comment attributes
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000) # Ensure content is not empty and has max length

# Schema for creating a new comment (input for POST requests)
class CommentCreate(CommentBase):
    # prompt_id and user_id will come from the URL path and authentication token respectively
    pass

# Schema for updating a comment (only content can be updated)
class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

# Schema for comment data returned in API responses (output)
class CommentResponse(CommentBase):
    comment_id: int
    prompt_id: int
    user_id: int
    created_at: datetime
    # We will manually populate this in the router to avoid N+1 issues
    author_username: Optional[str] = None # To display the username of the comment's author

    class Config:
        from_attributes = True # Enables ORM mode