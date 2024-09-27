import random
import sys
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from models.datamodels import Node, Sensor, NodeSensorLink
from joblib import Parallel, delayed

# Database setup
DATABASE_URL = "duckdb:///./aclima.db"
engine = create_engine(DATABASE_URL, connect_args={"read_only": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# List of sample sensor types and manufacturers
SENSOR_TYPES = ["PM2.5", "PM10", "NO2", "O3", "CO", "Temperature", "Humidity"]
MANUFACTURERS = ["Aclima", "SensorTech", "EnviroMonitor", "AirQuality Inc.", "ClimateTrack"]


def create_sample_sensor(sensor_type):
    return Sensor(
        serial_num=f"S{random.randint(1000, 9999)}",
        sensor_type=sensor_type,
        manufacturer=random.choice(MANUFACTURERS)
    )


def create_sample_node():
    return Node(
        serial_num=f"N{random.randint(1000, 9999)}",
        name=f"Node {random.randint(1, 1000)}"
    )


def create_db_and_tables():
    Base.metadata.create_all(bind=engine, checkfirst=True)


def create_entities(n: int):
    nodes = [create_sample_node() for _ in range(n)]
    return nodes


def populate_database(n: int):
    nodes = create_entities(n)

    session = SessionLocal()
    try:
        # Add nodes
        session.add_all(nodes)
        session.commit()

        # Create sensors and node-sensor links
        for node in nodes:
            # Randomly select 1 to 7 unique sensor types for this node
            node_sensor_types = random.sample(SENSOR_TYPES, random.randint(1, len(SENSOR_TYPES)))

            for sensor_type in node_sensor_types:
                sensor = create_sample_sensor(sensor_type)
                session.add(sensor)
                session.flush()  # This will assign an ID to the sensor

                link = NodeSensorLink(node_id=node.id, sensor_id=sensor.id)
                session.add(link)

        session.commit()

        print(f"Created {n} nodes with unique sensors.")

    finally:
        session.close()


def verify_data():
    session = SessionLocal()
    try:
        nodes = session.query(Node).all()
        for node in nodes:
            sensor_links = session.query(NodeSensorLink).filter(NodeSensorLink.node_id == node.id).all()
            sensor_types = set()
            for link in sensor_links:
                sensor = session.query(Sensor).filter(Sensor.id == link.sensor_id).first()
                sensor_types.add(sensor.sensor_type)
            print(f"Node {node.name} has {len(sensor_links)} sensors with {len(sensor_types)} unique types")
    finally:
        session.close()


def main(n: int):
    create_db_and_tables()
    populate_database(n)
    verify_data()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python populate_db.py <number_of_records>")
        sys.exit(1)

    try:
        n = int(sys.argv[1])
        if n < 1:
            raise ValueError("Number of records must be a positive integer")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    main(n)