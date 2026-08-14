from pydantic import BaseModel

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

    class Config:
        from_attributes = True