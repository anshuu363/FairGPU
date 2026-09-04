from fastapi import FastAPI,Depends,HTTPException
from .config import settings
from .database import engine, Base,get_db
from . import models,schemas
from sqlalchemy.orm import Session
from datetime import timezone,datetime
import asyncio

from .failure_detector import monitor_nodes
from contextlib import asynccontextmanager
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(monitor_nodes())

    yield


app = FastAPI(
    title="FairGPU Scheduler",
    lifespan=lifespan
)

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
@app.post("/nodes/{node_id}/gpus", response_model=schemas.GPUResponse)
def register_gpu(
    node_id: int,
    gpu: schemas.GPUCreate,
    db: Session = Depends(get_db)
):
    node = db.query(models.Node).filter(
        models.Node.id == node_id
    ).first()

    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    existing = db.query(models.GPU).filter(
        models.GPU.node_id == node_id,
        models.GPU.gpu_index == gpu.gpu_index
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="GPU already registered on this node"
        )

    db_gpu = models.GPU(
        node_id=node_id,
        gpu_index=gpu.gpu_index,
        model=gpu.model,
        memory_gb=gpu.memory_gb,
        status="free"
    )

    db.add(db_gpu)
    db.commit()
    db.refresh(db_gpu)

    return db_gpu



@app.post("/reserve", response_model=schemas.ReservationResponse)
def reserve_gpu(
    request: schemas.ReservationCreate,
    db: Session = Depends(get_db)
):
    free_gpu = db.query(models.GPU).filter(
        models.GPU.status == "free"
    ).first()

    if free_gpu is None:
        reservation = models.Reservation(
            user_name=request.user_name,
            gpu_id=None,
            status="pending"
        )

        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        return reservation

    reservation = models.Reservation(
        user_name=request.user_name,
        gpu_id=free_gpu.id,
        status="running",
        started_at=datetime.now(timezone.utc)
    )

    free_gpu.status = "busy"

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation

from datetime import datetime, timezone

@app.post("/release/{reservation_id}")
def release_gpu(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    reservation = db.query(models.Reservation).filter(
        models.Reservation.id == reservation_id
    ).first()

    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    gpu = db.query(models.GPU).filter(
        models.GPU.id == reservation.gpu_id
    ).first()

    if gpu is None:
        raise HTTPException(status_code=404, detail="GPU not found")

    reservation.status = "completed"
    reservation.completed_at = datetime.now(timezone.utc)

    pending = db.query(models.Reservation).filter(
        models.Reservation.status == "pending"
    ).order_by(models.Reservation.created_at).first()

    if pending:
        pending.gpu_id = gpu.id
        pending.status = "running"
        pending.started_at = datetime.now(timezone.utc)
        gpu.status = "busy"
    else:
        gpu.status = "free"

    db.commit()

    return {
        "message": "GPU released successfully",
        "gpu_id": gpu.id,
        "reservation_id": reservation.id
    }

from datetime import datetime, timezone, timedelta

@app.delete("/cleanup/completed")
def cleanup_completed_reservations(
    db: Session = Depends(get_db)
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    deleted = db.query(models.Reservation).filter(
        models.Reservation.status == "completed",
        models.Reservation.completed_at.isnot(None),
        models.Reservation.completed_at < cutoff
    ).delete(synchronize_session=False)

    db.commit()

    return {
        "message": "Cleanup completed",
        "deleted_records": deleted,
        "cutoff_date": cutoff.isoformat()
    }
from datetime import datetime, timezone
@app.post("/nodes/{node_id}/heartbeat")
def receive_heartbeat(
    node_id: int,
    heartbeat: schemas.HeartbeatRequest,
    db: Session = Depends(get_db)
    
):

    # 1. Find the node
    node = db.query(models.Node).filter(
        models.Node.id == node_id
    ).first()

    if not node:
        raise HTTPException(
            status_code=404,
            detail="Node not found"
        )

    # 2. Mark node as online
    node.status = "online"
    node.last_heartbeat = datetime.now(timezone.utc)
    # 3. Update the GPUs whose metrics were sent
    for gpu_data in heartbeat.gpus:

        gpu = db.query(models.GPU).filter(
            models.GPU.node_id == node_id,
            models.GPU.gpu_index == gpu_data.gpu_index
        ).first()

        if gpu:
            gpu.utilization_percent = gpu_data.utilization_percent
            gpu.memory_utilization_percent = (
                gpu_data.memory_utilization_percent
            )
            gpu.memory_used_gb = gpu_data.memory_used_gb

    # 4. Store heartbeat
    heartbeat_record = models.Heartbeat(
        node_id=node_id
    )

    db.add(heartbeat_record)
    # 5. Save changes
    db.commit()

    # 6. IMPORTANT:
    # Get ALL GPUs belonging to this node
    all_gpus = db.query(models.GPU).filter(
        models.GPU.node_id == node_id
    ).all()

    # 7. Return ALL GPUs
    return {
        "message": "Heartbeat received",
        "node_id": node_id,
        "status": node.status,
        "gpus": [
            {
                "gpu_id": gpu.id,
                "gpu_index": gpu.gpu_index,
                "model": gpu.model,
                "memory_gb": gpu.memory_gb,
                "status": gpu.status,
                "utilization_percent": gpu.utilization_percent,
                "memory_utilization_percent": (
                    gpu.memory_utilization_percent
                ),
                "memory_used_gb": gpu.memory_used_gb
            }
            for gpu in all_gpus
        ]
    }
@app.post("/nodes/register")
def register_node(
    node: schemas.NodeCreate,
    db: Session = Depends(get_db)
):
    existing_node = db.query(models.Node).filter(
        models.Node.hostname == node.hostname
    ).first()

    if existing_node:
        return existing_node

    new_node = models.Node(
        name=node.name,
        hostname=node.hostname,
        status="online"
    )

    db.add(new_node)
    db.commit()
    db.refresh(new_node)

    return new_node

@app.post("/nodes/{node_id}/gpus")
def register_gpu(
    node_id: int,
    gpu: schemas.GPUCreate,
    db: Session = Depends(get_db)
):

    node = db.query(models.Node).filter(
        models.Node.id == node_id
    ).first()

    if not node:
        raise HTTPException(
            status_code=404,
            detail="Node not found"
        )

    existing_gpu = db.query(models.GPU).filter(
        models.GPU.node_id == node_id,
        models.GPU.gpu_index == gpu.gpu_index
    ).first()

    if existing_gpu:
        return existing_gpu

    new_gpu = models.GPU(
        node_id=node_id,
        gpu_index=gpu.gpu_index,
        model=gpu.model,
        memory_gb=gpu.memory_gb,
        status="free"
    )

    db.add(new_gpu)
    db.commit()
    db.refresh(new_gpu)

    return new_gpu

