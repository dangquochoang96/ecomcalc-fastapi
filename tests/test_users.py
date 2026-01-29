from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_user():
    """Test creating a new user"""
    user_data = {
        "email": "test@example.com",
        "phone": "0123456789",
        "full_name": "Test User",
        "password": "hoang123!"
    }
    response = client.post("/api/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["phone"] == user_data["phone"]
    assert "id" in data


def test_get_users():
    """Test getting all users"""
    response = client.get("/api/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_user_not_found():
    """Test getting a non-existent user"""
    response = client.get("/api/users/999999")
    assert response.status_code == 404
