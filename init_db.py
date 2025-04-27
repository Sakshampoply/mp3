import os
import sys
from sqlalchemy import create_engine, text

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.resume import Base


def init_database():
    try:
        engine = create_engine(settings.POSTGRES_URL)

        with engine.connect() as conn:
            # Create vector extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

            # Create tables
            Base.metadata.create_all(engine)

        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
