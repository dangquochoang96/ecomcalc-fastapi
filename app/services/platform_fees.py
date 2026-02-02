from sqlalchemy.orm import Session
from app.models.platform_fees import PlatformFee, Platform


def get_all_platform_fees(db: Session):
    return db.query(PlatformFee).filter(PlatformFee.is_active).all()


def get_all_platform(db: Session):
    return db.query(Platform).filter(Platform.is_active).all()
