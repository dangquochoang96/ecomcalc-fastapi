from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+mysqlconnector://cp030657_dev:Hoang123*@118.27.202.139:3306/cp030657_ecomcalc"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env that aren't defined here


settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
