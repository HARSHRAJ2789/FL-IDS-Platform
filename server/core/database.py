from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from pathlib import Path

# Respect DATABASE_URL env var — fallback to local ./data/flds.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/flds.db")
WEIGHTS_DIR  = os.getenv("WEIGHTS_DIR",  "./data/weights")

# Ensure local data dirs exist (no-op in Docker where /data is a volume)
_db_path = DATABASE_URL.replace("sqlite:///", "").lstrip("/")
if DATABASE_URL.startswith("sqlite"):
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
Path(WEIGHTS_DIR).mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
