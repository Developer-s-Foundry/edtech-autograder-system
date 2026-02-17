import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"), future=True)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1")).scalar()
    print("DB OK:", result)
