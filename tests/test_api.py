import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models import User
from app.database import Base, engine, get_db
from sqlalchemy.orm import Session

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


def test_read_random_user_page():
    response = client.get("/random")
    assert response.status_code == 200


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
            "location": {
                "street": {"number": 123, "name": "Main St"},
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "postcode": "10001",
                "coordinates": {"latitude": "40.7128", "longitude": "-74.0060"},
                "timezone": {"offset": "-4:00", "description": "Eastern Time"}
            },
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
    assert "No users found" in response.json()["detail"]


def test_get_nonexistent_user():
    response = client.get("/api/user/999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_get_users_pagination():
    # Создаем тестового пользователя
    db = next(get_db())
    test_user = User(
        gender="male",
        first_name="Test",
        last_name="User",
        phone="123-456-7890",
        email="test@example.com",
        location={
            "street": {"number": 123, "name": "Test St"},
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
            "postcode": "12345",
            "coordinates": {"latitude": "0", "longitude": "0"},
            "timezone": {"offset": "+0:00", "description": "Test Timezone"}
        },
        picture={"thumbnail": "http://example.com/test.jpg"}
    )
    db.add(test_user)
    db.commit()

    # Тестируем пагинацию
    response = client.get("/api/users?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1
    assert data["total"] == 1 