from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings


DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# This creates the connection between Python and your database.
engine = create_engine(DATABASE_URL)

# A session is like a temporary conversation with the database.
# It creates new database sessions whenever needed.
sessionlocal = sessionmaker(bind = engine, autoflush=False, autocommit = False)


# Base converts normal Python classes into ORM models.
Base = declarative_base()


def get_db():
    
    db = sessionlocal()
    
    try:
        yield db
    
    finally:
        db.close()