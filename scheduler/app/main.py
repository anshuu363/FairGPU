from fastapi import FastAPI,Depends
from .config import settings
from .database import engine, Base,get_db
from . import models,schemas
from sqlalchemy.orm import Session

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

@app.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(
        name=user.name,
        email=user.email
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user