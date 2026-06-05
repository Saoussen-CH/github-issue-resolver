import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_all_sessions_returned_with_no_filter(client):
    res = client.get("/api/sessions")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["sessions"]) == 12


def test_filter_by_track_returns_matching_sessions(client):
    res = client.get("/api/sessions?track=AI+%26+ML")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["sessions"]) > 0, "Expected AI & ML sessions, got none"
    for s in data["sessions"]:
        assert s["track"] == "AI & ML", f"Got session from wrong track: {s['track']}"


def test_filter_by_day_returns_matching_sessions(client):
    res = client.get("/api/sessions?day=1")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["sessions"]) > 0, "Expected Day 1 sessions, got none"
    for s in data["sessions"]:
        assert s["day"] == 1, f"Got session from wrong day: {s['day']}"


def test_speaker_search_is_case_insensitive(client):
    res = client.get("/api/sessions?speaker=eric")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["sessions"]) > 0, "Search for 'eric' should match 'Eric Schmidt'"


def test_total_reflects_filtered_count(client):
    res = client.get("/api/sessions?track=Cloud")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == len(data["sessions"]), \
        f"total={data['total']} but got {len(data['sessions'])} sessions"
