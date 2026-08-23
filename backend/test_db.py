from sqlalchemy import text

from app.db.session import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"Database connection successful: {result.scalar()}")
except Exception as exc:
    print(f"Database connection failed: {exc}")