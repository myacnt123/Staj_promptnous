# app/schemas/label_schemas.py

from pydantic import BaseModel, Field

class LabelCreate(BaseModel):
    """Schema for creating a new label."""
    name: str = Field(..., min_length=1, max_length=50, description="The name of the label.")

class LabelResponse(BaseModel):
    """Schema for returning a label."""
    id: int
    name: str

    class Config:
        from_attributes = True # For Pydantic v2. For Pydantic v1, use orm_mode = True

class LabelUpdate(BaseModel):
    """Schema for updating a label."""
    name: str = Field(..., min_length=1, max_length=50, description="The name of the label.")