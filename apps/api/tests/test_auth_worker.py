from datetime import timedelta
from types import SimpleNamespace
import time
import uuid
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from apps.api.app import auth
from apps.api.app.config import settings
from apps.api.app.db import Job, now
from apps.api.app.worker import recover_expired
from conftest import create_session


def test_jwt_signature_expiry_issuer_audience(client, monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        auth, "jwks", SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key()))
    )
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    claims = {
        "sub": str(uuid.uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 120,
        "iss": "https://example.supabase.co/auth/v1",
        "aud": "authenticated",
    }

    def request(c, k=key):
        return client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + jwt.encode(c, k, algorithm="RS256")})

    assert request(claims).status_code == 200
    assert request({**claims, "exp": int(time.time()) - 10}).status_code == 401
    assert request({**claims, "aud": "wrong"}).status_code == 401
    assert request({**claims, "iss": "https://attacker.invalid"}).status_code == 401
    assert request(claims, rsa.generate_private_key(public_exponent=65537, key_size=2048)).status_code == 401


def test_expired_worker_lease_is_recovered(client, database):
    s = create_session(client)
    item = s["items"][0]
    user = client.get("/api/v1/auth/me").json()["id"]
    with database() as db:
        j = Job(
            user_id=user,
            item_id=item["id"],
            problem_version_id=item["problem_version_id"],
            code="x",
            code_hash="hash",
            mode="submit",
            status="running",
            request_id=str(uuid.uuid4()),
            lease_until=now() - timedelta(minutes=1),
        )
        db.add(j)
        db.commit()
        id = j.id
        recover_expired(db)
        db.refresh(j)
        assert j.status == "failed" and j.result["verdict"] == "System Error"
    assert client.get("/api/v1/executions/" + id).json()["status"] == "failed"


@pytest.mark.skipif(not settings.modal_token_id, reason="Modal credentials not configured")
def test_live_modal_is_explicit_opt_in():
    import os

    if os.getenv("RUN_LIVE_MODAL_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_MODAL_TESTS=1 to allow a billed sandbox smoke test")
    from apps.api.app.execution import ModalProvider

    provider = ModalProvider()
    id = provider.create_execution(
        {"code": "def solve(x): return x*2", "cases": [{"setup": "", "args": "3"}]}, lambda id: None
    )
    assert provider.get_execution_result(id)["outputs"][0]["value"] == 6
