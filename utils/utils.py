from database import SessionLocal


async def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
