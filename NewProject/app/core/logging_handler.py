import logging
from sqlalchemy.orm import Session
from app.database.models import AuditLog # Import your new AuditLog model
from app.database.database import SessionLocal # Import your production SessionLocal

class SQLAlchemyHandler(logging.Handler):
    """
    A custom logging handler that writes log records to a SQLAlchemy database table.
    """
    def emit(self, record: logging.LogRecord):
        # We need to create a new session for each log record
        # to ensure it's committed independently and doesn't interfere
        # with ongoing request transactions.
        # This is important for robustness if the main transaction fails.
        db: Session = SessionLocal() # Get a new session from your production SessionLocal
        try:
            # Extract data from the log record.
            # The 'msg' attribute of the LogRecord will be a dictionary
            # that we'll pass from our custom audit dependency.
            log_data = record.msg

            audit_entry = AuditLog(
                endpoint=log_data.get("endpoint", "N/A"),
                ip_address=log_data.get("ip_address", "N/A"),
                user_id=log_data.get("user_id"), # Will be None if unauthenticated
                username=log_data.get("username"), # Will be None if unauthenticated
                # timestamp will be defaulted by the model
            )
            db.add(audit_entry)
            db.commit()
        except Exception as e:
            # IMPORTANT: Log errors from the handler itself to prevent infinite loops or crashes
            # Fallback to console for handler errors
            print(f"ERROR: Failed to write audit log to DB: {e}", flush=True)
            db.rollback() # Rollback the session if an error occurs
        finally:
            db.close() # Always close the session