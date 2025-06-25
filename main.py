from fastapi import FastAPI
from app import models
from app.database import engine
from app.routers import users, notes

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notes API",
    description="REST API backend to manage user notes with JWT authentication.",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(notes.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Hello from FastAPI."}