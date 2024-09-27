import pytest
import requests
from typing import Dict

BASE_URL = "http://localhost:8002"

@pytest.fixture(scope="module")
def api_client():
    class APIClient:
        def __init__(self):
            self.base_url = BASE_URL
            self.sensor_id = None
            self.node_id = None

        def create_sensor(self, data: Dict):
            response = requests.post(f"{self.base_url}/sensors", json=data)
            if response.status_code == 200:
                self.sensor_id = response.json()["id"]
            return response

        def get_sensor(self, sensor_id: int):
            return requests.get(f"{self.base_url}/sensors/{sensor_id}")

        def list_sensors(self):
            return requests.get(f"{self.base_url}/sensors")

        def update_sensor(self, sensor_id: int, data: Dict):
            return requests.put(f"{self.base_url}/sensors/{sensor_id}", json=data)

        def create_node(self, data: Dict):
            response = requests.post(f"{self.base_url}/nodes", json=data)
            if response.status_code == 200:
                self.node_id = response.json()["id"]
            return response

        def get_node(self, node_id: int):
            return requests.get(f"{self.base_url}/nodes/{node_id}")

        def list_nodes(self):
            return requests.get(f"{self.base_url}/nodes")

        def connect_sensor_to_node(self, node_id: int, sensor_id: int):
            return requests.post(f"{self.base_url}/connect_sensor_to_node", params={"node_id": node_id, "sensor_id": sensor_id})

        def get_node_sensors(self, node_id: int):
            return requests.get(f"{self.base_url}/nodes/{node_id}/sensors")

    return APIClient()

def test_create_sensor(api_client):
    sensor_data = {
        "serial_num": "S1234",
        "sensor_type": "PM2.5",
        "manufacturer": "Aclima"
    }
    response = api_client.create_sensor(sensor_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["serial_num"] == sensor_data["serial_num"]
    assert response.json()["sensor_type"] == sensor_data["sensor_type"]
    assert response.json()["manufacturer"] == sensor_data["manufacturer"]

def test_get_sensor(api_client):
    response = api_client.get_sensor(api_client.sensor_id)
    assert response.status_code == 200
    assert response.json()["id"] == api_client.sensor_id

def test_list_sensors(api_client):
    response = api_client.list_sensors()
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_update_sensor(api_client):
    updated_data = {
        "serial_num": "S1234-updated",
        "sensor_type": "PM10",
        "manufacturer": "Aclima Inc."
    }
    response = api_client.update_sensor(api_client.sensor_id, updated_data)
    assert response.status_code == 200
    assert response.json()["serial_num"] == updated_data["serial_num"]
    assert response.json()["sensor_type"] == updated_data["sensor_type"]
    assert response.json()["manufacturer"] == updated_data["manufacturer"]

def test_create_node(api_client):
    node_data = {
        "serial_num": "N5678",
        "name": "Test Node"
    }
    response = api_client.create_node(node_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["serial_num"] == node_data["serial_num"]
    assert response.json()["name"] == node_data["name"]

def test_get_node(api_client):
    response = api_client.get_node(api_client.node_id)
    assert response.status_code == 200
    assert response.json()["id"] == api_client.node_id

def test_list_nodes(api_client):
    response = api_client.list_nodes()
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_connect_sensor_to_node(api_client):
    response = api_client.connect_sensor_to_node(api_client.node_id, api_client.sensor_id)
    assert response.status_code == 200
    assert response.json()["message"] == "Sensor connected to node successfully"

def test_get_node_sensors(api_client):
    response = api_client.get_node_sensors(api_client.node_id)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert any(sensor["id"] == api_client.sensor_id for sensor in response.json())

if __name__ == "__main__":
    pytest.main([__file__])