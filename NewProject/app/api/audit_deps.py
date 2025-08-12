# app/api/deps.py (add this function)
from fastapi import Request, Depends
from app.api.deps import get_current_user # Assuming you have this for authentication
from app.schemas.user import UserPublic # Assuming this is your schema for current_user
from app.core.logging_config import audit_logger # Import your audit logger

async def audit_request(
    request: Request,
    current_user: UserPublic | None = Depends(get_current_user) # Make it optional for unauthenticated requests
):
    """
    FastAPI dependency to capture audit information for each request.
    """
    endpoint = request.url.path
    ip_address = request.client.host if request.client else "N/A"
    user_id = current_user.id if current_user else None
    username = current_user.username if current_user else None

    # Log the audit data as a dictionary.
    # The SQLAlchemyHandler expects a dictionary in the record's 'msg' attribute.
    audit_logger.info({
        "endpoint": endpoint,
        "ip_address": ip_address,
        "user_id": user_id,
        "username": username
    })

    # This is a dependency, it just performs an action and doesn't return anything
    # that needs to be injected into the route function arguments.
    # You can return something if needed by other dependencies, but not required here.
    return None # Or just don't return anything