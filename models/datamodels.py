from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Sequence
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

Base = declarative_base()


# Models
class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, Sequence('sensor_id_seq'), server_default=Sequence('sensor_id_seq').next_value(),
                primary_key=True)
    serial_num = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    nodes = relationship("Node", secondary="node_sensor_links", back_populates="sensors")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, Sequence('node_id_seq'), server_default=Sequence('node_id_seq').next_value(), primary_key=True)
    serial_num = Column(String, nullable=False)
    name = Column(String, nullable=False)
    sensors = relationship("Sensor", secondary="node_sensor_links", back_populates="nodes")


class NodeSensorLink(Base):
    __tablename__ = "node_sensor_links"

    node_id = Column(Integer, ForeignKey("nodes.id"), primary_key=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), primary_key=True)


# Pydantic models for request/response
class SensorBase(BaseModel):
    serial_num: str
    sensor_type: str
    manufacturer: str


class SensorCreate(SensorBase):
    pass


class SensorResponse(SensorBase):
    id: int

    class Config:
        orm_mode = True


class NodeBase(BaseModel):
    serial_num: str
    name: str


class NodeCreate(NodeBase):
    pass


class NodeResponse(NodeBase):
    id: int

    class Config:
        orm_mode = True
