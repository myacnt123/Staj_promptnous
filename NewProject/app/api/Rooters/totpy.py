# app/routers/totp.py
import pyotp
import base64
import os
from fastapi import APIRouter, Depends, HTTPException , status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user
from app.database.database import get_db
from app.database.models import User
from pydantic import BaseModel


from app.schemas.user import UserInDB

router = APIRouter(
    prefix="/totp",
    tags=["Totp"],
)


@router.get("/totp/setup")
def setup_totp(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                      detail="TOTP çoktan aktive edildi")

    # Generate a new secret using a workaround
    secret = base64.b32encode(os.urandom(10)).decode('utf-8')[:16]

    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Your App"
    )

    return {"secret": secret, "qr_uri": qr_uri}


class TOTPVerify(BaseModel):
    code: str
    totp_secret: str


@router.post("/totp/verify-setup")
def verify_totp_setup(payload: TOTPVerify,
                      current_user: User = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    if  (current_user.totp_enabled == True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="TOTP çoktan aktive edildi")

    totp = pyotp.TOTP(payload.totp_secret)
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if totp.verify(payload.code):
        # Code is valid; update the SQLAlchemy model instance
        db_user.totp_enabled = True
        db_user.totp_secret = payload.totp_secret

        # Now commit the changes to the database
        db.commit()
        db.refresh(db_user)

        return {"message": "TOTP has been successfully enabled."}

    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        detail="TOTP kodu yanlış.")


@router.delete("/totp/deactivate")
def deactivate_totp(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Deactivates TOTP for the authenticated user.
    """
    if not current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Aktive edilmiş bir TOTP bulunmuyor")

    db_user = db.query(User).filter(User.id == current_user.id).first()
    # Set totp_enabled to False and clear the secret
    db_user.totp_enabled = False
    db_user.totp_secret = None

    db.commit()
    db.refresh(db_user)

    return {"message": "TOTP has been successfully deactivated.","status": 200}

@router.get("/totp/iftotp")
def totp_iftotp(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    if  current_user.totp_enabled:
        return True
    return False
