# my_fastapi_angular_backend_v2/app/api/routers/comments.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import crud, models  # Import models for type checking db_objects
from app.schemas import comment as comment_schemas
from app.schemas import user as user_schemas  # Needed for get_current_active_user's return type

from app.api.deps import get_current_active_user
from app.database.database import get_db
from app.api.audit_deps import audit_request
router = APIRouter(
    tags=["Comments"],  # Tag for OpenAPI/Swagger UI
)


# --- Endpoint 1: Create a Comment for a Specific Prompt ---
# Path: /prompts/{prompt_id}/comments (nested under prompts)
@router.post("/prompts/{prompt_id}/comments", response_model=comment_schemas.CommentResponse,
             status_code=status.HTTP_201_CREATED)
async def create_comment_for_prompt(
        prompt_id: int,
        comment: comment_schemas.CommentCreate,
        current_user: user_schemas.UserInDB = Depends(get_current_active_user),  # Requires authentication
        db: Session = Depends(get_db)
):
    """
    Create a new comment for a specific prompt.
    Requires authentication.
    """
    # First, check if the prompt exists
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    db_comment = crud.create_comment(db, comment=comment, user_id=current_user.id, prompt_id=prompt_id)

    # Populate author_username for the response (N+1 query here if not eager loaded)
    db_comment.author_username = current_user.username

    return db_comment


# --- Endpoint 2: Get All Comments for a Specific Prompt ---
# Path: /prompts/{prompt_id}/comments (list all comments for a prompt)
@router.get("/prompts/{prompt_id}/comments", response_model=List[comment_schemas.CommentResponse])
async def get_comments_for_prompt_endpoint(
        prompt_id: int,
        db: Session = Depends(get_db),  # Public endpoint, no authentication needed
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve all comments for a specific prompt. Publicly accessible.
    Author usernames are included for display.
    """
    # Optional: Check if the prompt exists (if you want 404 for non-existent prompt IDs)
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    comments = crud.get_comments_for_prompt(db, prompt_id=prompt_id, skip=skip, limit=limit)

    # IMPORTANT: Populating author_username for each comment
    # This loop will trigger an N+1 query problem if not using joinedload.
    # For a comments section, displaying the author is typically essential,
    # so this is a common trade-off if you explicitly avoid joinedload.
    for comment in comments:
        if comment.user:  # Ensure user relationship is loaded (triggers query if not)
            comment.author_username = comment.user.username
        else:
            comment.author_username = None  # Fallback if user somehow doesn't exist (e.g., deleted)

    return comments


# --- Endpoint 3: Get a Single Comment by ID ---
# Path: /comments/{comment_id}
@router.get("/comments/{comment_id}", response_model=comment_schemas.CommentResponse)
async def get_comment_by_id_endpoint(
        comment_id: int,
        db: Session = Depends(get_db)  # Publicly accessible
):
    """
    Retrieve a single comment by its ID.
    Author username is included for display.
    """
    db_comment = crud.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Populate author_username (N+1 query here if not eager loaded)
    if db_comment.user:
        db_comment.author_username = db_comment.user.username
    else:
        db_comment.author_username = None

    return db_comment


# --- Endpoint 4: Update a Comment ---
# Path: /comments/{comment_id}
@router.put("/comments/{comment_id}", response_model=comment_schemas.CommentResponse)
async def update_comment_endpoint(
        comment_id: int,
        comment_update: comment_schemas.CommentUpdate,
        current_user: user_schemas.UserInDB = Depends(get_current_active_user),  # Requires authentication
        db: Session = Depends(get_db)
):
    """
    Update the content of an existing comment.
    Only the author of the comment can update it.
    """
    db_comment = crud.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yorum bulunamadı")

    # Authorization check: Only the comment's author can update it
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu yorumu silmek için gerekli yetkilere sahip değilsiniz")

    updated_comment = crud.update_comment(db, comment_id=comment_id, comment_update=comment_update)
    if not updated_comment:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Yorumu güncelleme işlemi başarısız oldu.")

    # Populate author_username for the response
    updated_comment.author_username = current_user.username  # Since it's the current user updating

    return updated_comment


# --- Endpoint 5: Delete a Comment ---
# Path: /comments/{comment_id}
@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_endpoint(
        comment_id: int,
        current_user: user_schemas.UserInDB = Depends(get_current_active_user),  # Requires authentication
        db: Session = Depends(get_db)
):
    """
    Delete a comment.
    Only the author of the comment can delete it. (Admin check logic is at admin page).
    """
    db_comment = crud.get_comment(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yorum bulunamadı")

    # Authorization check: Only the comment's author can delete it
    # Future: if db_comment.user_id != current_user.id and not current_user.is_admin:
    if db_comment.user_id != current_user.id and current_user.id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu yorumu silmek için yetkili değilsiniz")

    success = crud.delete_comment(db, comment_id=comment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Yorum silinemedi")

    return Response(status_code=status.HTTP_204_NO_CONTENT)