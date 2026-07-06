"""
Database configuration.
Uses SQLite for simplicity - the whole database lives in one file: finance.db
You can swap SQLALCHEMY_DATABASE_URL for a Postgres/MySQL URL later without
changing any other code, since we only use the SQLAlchemy ORM layer.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./finance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
