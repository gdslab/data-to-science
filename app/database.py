import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# postgres environment variables
pg_host = os.environ.get("POSTGRES_HOST", None)
pg_user = os.environ.get("POSTGRES_USER", None)
pg_pass = os.environ.get("POSTGRES_PASSWORD", None)
pg_db = os.environ.get("POSTGRES_DB", None)

SQLALCHEMY_DATABASE_URL = f"postgresql://{pg_user}:{pg_pass}@{pg_host}/{pg_db}"

# create dialect and pool for communicating with postgresql database
engine = create_engine(SQLALCHEMY_DATABASE_URL)
# SessionLocal class will be used to establish database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base class that will be used by database models
Base = declarative_base()
