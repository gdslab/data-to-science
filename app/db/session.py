from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# create dialect and pool for communicating with postgresql database
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
# SessionLocal class will be used to establish database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
