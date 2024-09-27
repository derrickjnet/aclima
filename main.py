import asyncio
import json
import random
import time
import signal
from collections.abc import AsyncIterator
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from sqlalchemy import select, func, distinct
from models.datamodels import Sensor, SensorCreate, SensorResponse, Node, NodeResponse, NodeCreate, NodeSensorLink
from models.config import SessionLocal, get_db, init_db



@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend, prefix="fastapi-cache")
    yield


app = FastAPI(lifespan=lifespan)

app = FastAPI()

is_shutting_down = False

def signal_handler(signum, frame):
    global is_shutting_down
    is_shutting_down = True
    print("Shutdown signal received. Closing connections...")

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


# API routes
@app.post("/sensors", response_model=SensorResponse)
async def create_sensor(sensor: SensorCreate, db: SessionLocal = Depends(get_db)):
    db_sensor = Sensor(**sensor.dict())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


@cache(expire=600)
@app.get("/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor(sensor_id: int, db: SessionLocal = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


@app.get("/sensors", response_model=List[SensorResponse])
async def list_sensors(db: SessionLocal = Depends(get_db)):
    start = time.time()
    sensors = db.query(Sensor).all()
    print(f'Sensors Fetch: {time.time() - start}')
    return sensors


@app.post("/nodes", response_model=NodeResponse)
async def create_node(node: NodeCreate, db: SessionLocal = Depends(get_db)):
    db_node = Node(**node.dict())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node


@cache(expire=600)
@app.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, db: SessionLocal = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@app.get("/nodes", response_model=List[NodeResponse])
async def list_nodes(db: SessionLocal = Depends(get_db)):
    start = time.time()
    nodes = db.query(Node).all()
    print(f'Nodes Fetch: {time.time() - start}')
    return nodes


@app.post("/connect_sensor_to_node")
async def connect_sensor_to_node(node_id: int, sensor_id: int, db: SessionLocal = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not node or not sensor:
        raise HTTPException(status_code=404, detail="Node or Sensor not found")

    link = NodeSensorLink(node_id=node_id, sensor_id=sensor_id)
    db.add(link)
    db.commit()
    return {"message": "Sensor connected to node successfully"}


@cache(expire=600)
@app.put("/sensors/{sensor_id}", response_model=SensorResponse)
async def update_sensor(sensor_id: int, sensor_update: SensorCreate, db: SessionLocal = Depends(get_db)):
    db_sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not db_sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    for key, value in sensor_update.dict().items():
        setattr(db_sensor, key, value)

    db.commit()
    db.refresh(db_sensor)
    return db_sensor


@cache(expire=600)
@app.get("/nodes/{node_id}/sensors", response_model=List[SensorResponse])
async def get_node_sensors(node_id: int, db: SessionLocal = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    return node.sensors


@app.get("/nodes_sensors_count")
def get_nodes_sensors_count(db: SessionLocal = Depends(get_db)):
    start = time.time()
    query = (
        select(Node.id, func.count(NodeSensorLink.node_id).label("sensor_count"))
        .outerjoin(NodeSensorLink)
        .group_by(Node.id)
    )
    result = db.execute(query).all()
    print(f'Sensor Count Fetch: {time.time() - start}')
    return {node_id: sensor_count for node_id, sensor_count in result}


@app.get("/sensor_summary")
@cache(expire=300)  # Cache for 5 minutes
async def get_sensor_summary(db: SessionLocal = Depends(get_db)):
    # Efficient query to get total sensors and sensor type distribution in one go
    query = select(
        func.count(distinct(Sensor.id)).label("total_sensors"),
        Sensor.sensor_type,
        func.count(Sensor.sensor_type).label("type_count")
    ).group_by(Sensor.sensor_type)

    result = db.execute(query).fetchall()

    total_sensors = 0
    type_distribution = {}

    for row in result:
        total_sensors += row.type_count
        type_distribution[row.sensor_type] = row.type_count

    return {
        "total_sensors": total_sensors,
        "type_distribution": type_distribution
    }


@app.get("/node_summary")
@cache(expire=300)  # Cache for 5 minutes
async def get_node_summary(db: SessionLocal = Depends(get_db)):
    # Efficient query to get total nodes and node complexity distribution in one go
    query = select(
        func.count(distinct(Node.id)).label("total_nodes"),
        func.count(NodeSensorLink.sensor_id).label("sensor_count"),
        func.count(Node.id).label("node_count")
    ).outerjoin(NodeSensorLink).group_by(Node.id)

    result = db.execute(query).fetchall()

    total_nodes = 0
    complexity_distribution = defaultdict(int)

    for row in result:
        total_nodes += 1
        complexity_distribution[row.sensor_count] += 1

    return {
        "total_nodes": total_nodes,
        "complexity_distribution": dict(complexity_distribution)
    }


@app.get("/sensor_type_distribution")
async def get_sensor_type_distribution(db: SessionLocal = Depends(get_db)):
    start = time.time()
    query = select(Sensor.sensor_type, func.count(Sensor.id)).group_by(Sensor.sensor_type)
    result = db.execute(query).fetchall()
    distribution = {sensor_type: count for sensor_type, count in result}
    print(f'Sensor Type Distro Fetch: {time.time() - start}')
    return distribution


@app.get("/node_complexity_distribution")
async def get_node_complexity_distribution(db: SessionLocal = Depends(get_db)):
    start = time.time()
    query = select(
        func.count(NodeSensorLink.sensor_id).label("sensor_count"),
        func.count(Node.id).label("node_count")
    ).outerjoin(NodeSensorLink).group_by(Node.id)
    result = db.execute(query).fetchall()

    distribution = defaultdict(int)
    for row in result:
        distribution[row.sensor_count] += 1
    print(f'Node Complexity Distro Fetch: {time.time() - start}')

    return dict(distribution)


@app.get("/stream_sensor_data")
async def stream_sensor_data():
    async def event_generator():
        sensor_data_history = defaultdict(list)
        max_data_points = 30

        while True:
            if is_shutting_down:
                break

            sensor_data = {
                "PM2.5": random.uniform(0, 100),
                "PM10": random.uniform(0, 150),
                "NO2": random.uniform(0, 200),
                "O3": random.uniform(0, 100),
                "CO": random.uniform(0, 50),
                "Temperature": random.uniform(-10, 40),
                "Humidity": random.uniform(0, 100)
            }

            timestamp = time.strftime("%H:%M:%S")

            for sensor_type, value in sensor_data.items():
                sensor_data_history[sensor_type].append({"x": timestamp, "y": value})
                if len(sensor_data_history[sensor_type]) > max_data_points:
                    sensor_data_history[sensor_type].pop(0)

            response_data = {
                "current": sensor_data,
                "history": dict(sensor_data_history)
            }

            yield f"data: {json.dumps(response_data)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")



# Web interface routes
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.on_event("startup")
def on_startup():
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    global is_shutting_down
    is_shutting_down = True
    print("Application is shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
