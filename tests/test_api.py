import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models import User
from app.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Random Users API" in response.text

@patch('httpx.AsyncClient.get')
async def test_load_users(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [{
            "gender": "male",
            "name": {"first": "John", "last": "Doe"},
            "phone": "123-456-7890",
            "email": "john@example.com",
            "location": {"city": "New York", "country": "USA"},
            "picture": {"thumbnail": "http://example.com/thumb.jpg"}
        }]
    }
    mock_get.return_value = mock_response

    response = client.post("/api/users/load", json={"count": 1})
    assert response.status_code == 200
    assert "Successfully loaded" in response.json()["message"]

def test_get_users_empty():
    response = client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 0
    assert data["total"] == 0

def test_get_random_user_empty():
    response = client.get("/api/random")
    assert response.status_code == 404
    assert "No users in database" in response.json()["detail"]

def test_get_nonexistent_user():
    response = client.get("/api/user/999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"] 