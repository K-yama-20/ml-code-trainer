# ruff: noqa: E402
from pathlib import Path
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from apps.api.app.db import Base, db_session
from apps.api.app.main import app


@pytest.fixture
def database(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    monkeypatch.setattr("apps.api.app.main.init_db", lambda: None)
    sessions = sessionmaker(engine, expire_on_commit=False)

    def override():
        with sessions() as db:
            yield db

    app.dependency_overrides[db_session] = override
    yield sessions
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client(database):
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/guest").status_code == 200
        yield client


@pytest.fixture(autouse=True)
def workspace_temp():
    path = ROOT / "artifacts" / "tmp"
    path.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(path)


def create_session(client, concept="NP05", **options):
    response = client.post("/api/v1/sessions", json={"kind": "custom", "concept_id": concept, "count": 6, **options})
    assert response.status_code == 200, response.text
    return response.json()
