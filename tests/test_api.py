import os
from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # basic sanity: one known activity exists
    assert "Chess Club" in data


def test_signup_and_unregister():
    activity = "Chess Club"
    email = "testuser@example.com"

    # ensure clean start: if present, remove
    resp = client.get("/activities")
    assert resp.status_code == 200
    participants = resp.json()[activity]["participants"]
    if email in participants:
        del_resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
        assert del_resp.status_code == 200

    # sign up
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # verify present
    resp = client.get("/activities")
    participants = resp.json()[activity]["participants"]
    assert email in participants

    # unregister
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # verify removed
    resp = client.get("/activities")
    participants = resp.json()[activity]["participants"]
    assert email not in participants


import pytest
from urllib.parse import quote

from httpx import AsyncClient, ASGITransport

from src.app import app


@pytest.mark.asyncio
async def test_get_activities():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/activities")
        assert r.status_code == 200
        data = r.json()
        # basic sanity checks
        assert isinstance(data, dict)
        assert "Chess Club" in data


@pytest.mark.asyncio
async def test_signup_and_unregister():
    activity = "Chess Club"
    email = "testuser@example.com"
    activity_quoted = quote(activity, safe="")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # sign up
        r = await ac.post(f"/activities/{activity_quoted}/signup?email={quote(email, safe='')}")
        assert r.status_code == 200
        data = r.json()
        assert "Signed up" in data.get("message", "")

        # duplicate signup should return 400
        r2 = await ac.post(f"/activities/{activity_quoted}/signup?email={quote(email, safe='')}")
        assert r2.status_code == 400

        # unregister
        r3 = await ac.delete(f"/activities/{activity_quoted}/participants?email={quote(email, safe='')}")
        assert r3.status_code == 200

        # unregistering again should return 404
        r4 = await ac.delete(f"/activities/{activity_quoted}/participants?email={quote(email, safe='')}")
        assert r4.status_code == 404
