"""
Script to initialize the database tables.
Run this script separately if you need to create the database tables manually.
"""

from app.database import engine, Base


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()