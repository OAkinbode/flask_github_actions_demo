import pytest
from app import app as flask_app  # Rename the import to avoid confusion

@pytest.fixture
def client():
    # Use the imported app instance
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    # Make sure these match exactly what your Flask app returns!
    assert b'Hello from Flask!' in response.data

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_info(client):
    response = client.get('/api/info')
    assert response.status_code == 200
    assert 'app' in response.json
    assert 'version' in response.json
    assert response.json['version'] == '1.0.0'