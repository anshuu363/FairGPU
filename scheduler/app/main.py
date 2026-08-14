from fastapi import FastAPI,Depends,HTTPException
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
@app.get("/users", response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@app.post("/nodes/register", response_model=schemas.NodeResponse)
def register_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Node).filter(
        models.Node.name == node.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Node already registered"
        )

    db_node = models.Node(
        name=node.name,
        hostname=node.hostname,
        status="online"
    )

    db.add(db_node)
    db.commit()
    db.refresh(db_node)

    return db_node