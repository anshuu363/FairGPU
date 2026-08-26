from pydantic import BaseModel
from typing import List
from datetime import timezone,datetime
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class NodeCreate(BaseModel):
    name: str
    hostname: str


class NodeResponse(BaseModel):
    id: int
    name: str
    hostname: str
    status: str

    class Config:
        from_attributes = True

class GPUCreate(BaseModel):
    gpu_index: int
    model: str
    memory_gb: int


class GPUResponse(BaseModel):
    id: int
    node_id: int
    gpu_index: int
    model: str
    memory_gb: int
    status: str
    utilization_percent: float
    memory_utilization_percent: float
    memory_used_gb: float
    class Config:
        from_attributes = True

class ReservationCreate(BaseModel):
    user_name: str


class ReservationResponse(BaseModel):
    id: int
    user_name: str
    gpu_id: int
    status: str

    class Config:
        from_attributes = True

class GPUHeartbeat(BaseModel):
    gpu_index: int

    utilization_percent: float

    memory_utilization_percent: float

    memory_used_gb: float


class HeartbeatRequest(BaseModel):
    gpus: List[GPUHeartbeat]
    
class NodeCreate(BaseModel):
    name: str
    hostname: str



