import sys
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

_platform_root = Path(__file__).resolve().parent.parent
load_dotenv(_platform_root / ".env")
load_dotenv(_platform_root / "app" / ".env")

if str(_platform_root) not in sys.path:
    sys.path.insert(0, str(_platform_root))

from app.db_settings import resolve_database_url

# Connecting Database
while True:
    try:
        conn = psycopg2.connect(
            resolve_database_url(),
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