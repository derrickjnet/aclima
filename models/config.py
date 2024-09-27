from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from models.datamodels import Base

DATABASE_URL = "duckdb:///aclima.db"
engine = create_engine(DATABASE_URL, connect_args={"read_only": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()