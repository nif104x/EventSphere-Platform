from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = FastAPI()


while True:
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="",
            user="postgres",
            password="2020",
            cursor_factory=RealDictCursor,
        )
        cursor = conn.cursor()
        print("Database connection was successful!")
        break
    except Exception as error:
        print("Connecting to database failed")
        print("Error: ", error)
        time.sleep(2)


@app.get("/")
def admin_panel():
    return {"message": "Hello World"}
