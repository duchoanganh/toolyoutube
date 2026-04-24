import pytest
import json
import os
from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_render_missing_json(client):
    """Test /api/render without sending JSON payload"""
    response = client.post('/api/render')
    assert response.status_code == 415

def test_render_empty_scenes(client):
    """Test /api/render with empty scenes array"""
    payload = {
        "title": "UnitTest Theme",
        "scenes": []
    }
    response = client.post('/api/render', json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'video_url' in data

def test_download_endpoint(client):
    """Test the /api/download endpoint"""
    response = client.get('/api/download')
    # Can be 200 if the zip exists from previous render, or 404 if missing
    assert response.status_code in [200, 404]

def test_open_folder_endpoint(client):
    """Test the /api/open-folder endpoint"""
    response = client.post('/api/open-folder')
    # Should always return 200 success if os.startfile/subprocess succeeds
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
