# db.py
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv("config.env")

def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )

COHORT_CODE = os.getenv("COHORT_CODE")
