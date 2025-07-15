from fastapi import FastAPI
from .db.session import engine
from .db import models
from .api.api import api_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"Hello": "World"}
