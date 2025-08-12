import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.logging_handler import SQLAlchemyHandler # Import your new handler

# Define general log file path (for application internal logs, not audit)
LOG_DIR = "logs"
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
os.makedirs(LOG_DIR, exist_ok=True)

# Main application logger
main_logger = logging.getLogger("my_fastapi_app")
audit_logger = logging.getLogger("audit_logger") # Dedicated logger for audit events

def setup_logging():
    """
    Configures the logging system for the application, including a database handler for audit.
    """
    # --- Main Application Logger Configuration ---
    main_logger.setLevel(logging.DEBUG)
    if main_logger.hasHandlers():
        main_logger.handlers.clear()

    # Console Handler for main app logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s:     %(name)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    main_logger.addHandler(console_handler)

    # File Handler for main app logs
    file_handler = RotatingFileHandler(
        APP_LOG_FILE, maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    main_logger.addHandler(file_handler)
    main_logger.propagate = False # Prevent main app logs from going to root logger

    # --- Audit Logger Configuration ---
    audit_logger.setLevel(logging.INFO) # Audit logs usually INFO or higher
    if audit_logger.hasHandlers():
        audit_logger.handlers.clear()

    # Add the custom SQLAlchemy Handler to the audit logger
    db_handler = SQLAlchemyHandler()
    db_handler.setLevel(logging.INFO) # Only INFO and higher for audit logs
    audit_logger.addHandler(db_handler)
    audit_logger.propagate = False # Prevent audit logs from going to root logger

    # Optional: Configure logging for specific libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

# Call setup_logging when this module is imported
setup_logging()