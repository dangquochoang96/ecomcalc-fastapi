from sqlalchemy.orm import Session
from app.models.platform_fees import PlatformFee


def get_all_platform_fees(db: Session):
    return db.query(PlatformFee).filter(PlatformFee.is_active).all()
