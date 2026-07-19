"""Pagination behaviour for list endpoints (v0.0.8): the Page envelope,
limit/offset slicing, parameter validation, and ordering."""

from app.models import Course


def _register_and_login(client, username="pager", email="pager@example.com"):
    client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "password1234"},
    )
    response = client.post("/auth/login", data={"username": username, "password": "password1234"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_courses_pagination_envelope(client):
    response = client.get("/courses")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["items"][0]["title"] == "Spanish for Beginners"


def test_courses_limit_and_offset_slice_results(client, session):
    session.add(Course(language_code="fr", title="French Basics", level="A1", description="x"))
    session.add(Course(language_code="de", title="German Basics", level="A1", description="x"))
    session.commit()

    page = client.get("/courses?limit=2&offset=1").json()
    assert page["total"] == 3
    assert [course["title"] for course in page["items"]] == ["French Basics", "German Basics"]


def test_pagination_params_are_validated(client):
    assert client.get("/courses?limit=0").status_code == 422
    assert client.get("/courses?limit=101").status_code == 422
    assert client.get("/courses?offset=-1").status_code == 422


def test_translation_history_is_paginated_newest_first(client):
    headers = _register_and_login(client)
    for text in ["one", "two", "three"]:
        client.post(
            "/translate",
            headers=headers,
            json={"text": text, "source_lang": "en", "target_lang": "es"},
        )

    first = client.get("/translate/history?limit=2", headers=headers).json()
    assert first["total"] == 3
    assert [item["source_text"] for item in first["items"]] == ["three", "two"]

    second = client.get("/translate/history?limit=2&offset=2", headers=headers).json()
    assert [item["source_text"] for item in second["items"]] == ["one"]
