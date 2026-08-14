from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .database import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    hostname = Column(String, unique=True, nullable=False)
    status = Column(String, default="offline")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    gpus = relationship("GPU", back_populates="node")
    heartbeats = relationship("Heartbeat", back_populates="node")


class GPU(Base):
    __tablename__ = "gpus"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"))
    gpu_index = Column(Integer, nullable=False)
    model = Column(String, nullable=False)
    memory_gb = Column(Integer)
    status = Column(String, default="free")

    node = relationship("Node", back_populates="gpus")
    reservations = relationship("Reservation", back_populates="gpu")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    gpu_id = Column(Integer, ForeignKey("gpus.id"))
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    gpu = relationship("GPU", back_populates="reservations")
    job = relationship("Job", back_populates="reservation", uselist=False)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"))
    process_id = Column(Integer)
    status = Column(String, default="running")
    started_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    reservation = relationship("Reservation", back_populates="job")


class Heartbeat(Base):
    __tablename__ = "heartbeats"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"))
    gpu_utilization = Column(Integer)
    memory_utilization = Column(Integer)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    node = relationship("Node", back_populates="heartbeats")