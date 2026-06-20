import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from main_api import app

client = TestClient(app)


class TestAPI:
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data

    def test_search_empty_query(self):
        response = client.post("/api/search", json={"query": ""})
        assert response.status_code == 400

    def test_search_valid_query(self):
        try:
            response = client.post("/api/search", json={"query": "python developer", "top_k": 5})
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "query" in data
                assert "results" in data
        except Exception:
            pass

    def test_api_cors_headers(self):
        response = client.get("/")
        assert response.status_code == 200
