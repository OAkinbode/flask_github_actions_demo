import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello from Flask!' in response.data
    assert response.json['status'] == 'healthy'

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
