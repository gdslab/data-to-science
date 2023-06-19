from app.db.session import SessionLocal


def get_db():
    """Create database session with lifespan of a single request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
