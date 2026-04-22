import os
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv(Path(__file__).resolve().parent.parent / "app" / ".env")

_db_host = os.getenv("DB_HOST", "localhost")
_db_port = int(os.getenv("DB_PORT", "5432"))
_db_name = os.getenv("DB_NAME", "eventsphere")
_db_user = os.getenv("DB_USER", "postgres")
_db_password = os.getenv("DB_PASSWORD", "2020")

# Connecting Database
while True:
    try:
        conn = psycopg2.connect(
            host=_db_host,
            port=_db_port,
            database=_db_name,
            user=_db_user,
            password=_db_password,
            cursor_factory=RealDictCursor,
        )
        cursor = conn.cursor()
        print('Successfully connected database')
        break
    except Exception as error:
        print('Database connection Failed!!!!!!!')
        print("Error:", error)
        time.sleep(2)

def homePage():
    cursor.execute(
        """
        select * from user_main
        """
    )
    data = cursor.fetchall()
    return {"Hello": data}