from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# create dialect and pool for communicating with postgresql database
DB_URI = settings.SQLALCHEMY_DATABASE_URI
if DB_URI:
    engine = create_engine(DB_URI.unicode_string(), pool_pre_ping=True)
    # SessionLocal class will be used to establish database sessions
    SessionLocal = sessionmaker(autoflush=False, bind=engine)
