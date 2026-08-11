from fastapi import FastAPI
from .config import settings
from .database import engine, Base
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

@app.get("/")
async def root():
    return {"message": f"{settings.app_name} is running",
            "environment":settings.environment}

@app.get("/health")
async def health():
    return {"status": "healthy",
            "heartbeat interval":settings.heartbeat_interval
            }