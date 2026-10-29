import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.database import init_db

init_db()
client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "app_name" in data

def test_api_models_status():
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.json()
    assert "detector" in data
    assert "density_model" in data
    assert "tracker" in data

def test_api_system_status():
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert "platform" in data
    assert "torch_version" in data

def test_api_video_files():
    res = client.get("/api/video/files")
    assert res.status_code == 200
    data = res.json()
    assert "videos" in data

def test_api_analytics_current():
    res = client.get("/api/analytics/current")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data

def test_api_regions_and_lines():
    res = client.get("/api/analytics/regions")
    assert res.status_code == 200
    data = res.json()
    assert "regions" in data
    assert "lines" in data

def test_api_experiments_list():
    res = client.get("/api/experiments")
    assert res.status_code == 200
    data = res.json()
    assert "experiments" in data
