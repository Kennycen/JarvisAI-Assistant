from __future__ import annotations


def test_profile_starts_empty(client) -> None:
    res = client.get("/api/profile")
    assert res.status_code == 200
    body = res.json()
    assert body["preferred_name"] == ""
    assert body["about"] == ""


def test_profile_round_trip(client) -> None:
    payload = {
        "preferred_name": "Kenny",
        "location": "New York",
        "occupation": "Engineer",
        "about": "Builds assistants.",
        "preferences": "Be terse.",
    }
    written = client.put("/api/profile", json=payload)
    assert written.status_code == 200
    assert written.json()["preferred_name"] == "Kenny"

    loaded = client.get("/api/profile")
    assert loaded.json() == payload


def test_profile_rejects_overlong_about(client) -> None:
    res = client.put("/api/profile", json={"about": "x" * 4001})
    assert res.status_code == 422
