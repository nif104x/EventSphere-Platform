from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def homePage():
    return {"Hello": "World"}


