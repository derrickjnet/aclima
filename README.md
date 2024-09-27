# Aclima API with Vue.js Frontend

This project consists of a RESTful API for managing Aclima nodes and sensors, built with FastAPI and DuckDB, and a Vue.js frontend for interacting with the API.

## Prerequisites

- Python 3.7+
- pip
- Docker (optional)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/derrickjnet/aclima.git
   cd aclima
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the API

### Using Python

Start the FastAPI server:
```
uvicorn main:app --reload
```

### Using Docker

1. Build the Docker image:
   ```
   docker build -t aclima-api .
   ```

2. Run the Docker container:
   ```
   docker run -p 8000:8000 aclima-api
   ```

The API and web interface will be available at `http://localhost:8000`

## API Endpoints

- `GET /`: Serve the main HTML page
- `GET /sensors`: List all sensors
- `GET /sensors/{sensor_id}`: Get a specific sensor
- `POST /sensors`: Create a new sensor
- `GET /nodes`: List all nodes
- `GET /nodes/{node_id}`: Get a specific node
- `POST /nodes`: Create a new node
- `GET /nodes/{node_id}/sensors`: Get sensors connected to a specific node
- `POST /connect_sensor_to_node`: Connect a sensor to a node
- `GET /counts`: Get counts of sensors and nodes

## Web Interface Features

- Dashboard displaying count of sensors and nodes
- View list of sensors and nodes
- Fetch updated lists of sensors and nodes

## Notes

- The database is stored in `aclima.db` in the project root directory.
- DuckDB is used as the database engine, providing fast in-process analytics.
- The frontend uses Vue.js 2.6 and is embedded in the HTML template served by FastAPI.
- Bootstrap is used for styling the web interface.