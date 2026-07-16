import pytest

from app.services.spaced_repetition import DEFAULT_EASE_FACTOR, compute_next_schedule


# --- Pure unit tests for the SM-2 scheduling math ---


def test_first_review_good_recall_schedules_tomorrow_plus_one():
    outcome = compute_next_schedule(
        quality=5, repetitions=0, ease_factor=DEFAULT_EASE_FACTOR, interval_days=0
    )
    assert outcome.repetitions == 1
    assert outcome.interval_days == 1
    assert outcome.ease_factor > DEFAULT_EASE_FACTOR  # a perfect recall raises ease


def test_second_consecutive_good_recall_schedules_six_days():
    first = compute_next_schedule(
        quality=5, repetitions=0, ease_factor=DEFAULT_EASE_FACTOR, interval_days=0
    )
    second = compute_next_schedule(
        quality=5,
        repetitions=first.repetitions,
        ease_factor=first.ease_factor,
        interval_days=first.interval_days,
    )
    assert second.repetitions == 2
    assert second.interval_days == 6


def test_third_consecutive_good_recall_multiplies_by_ease_factor():
    state = compute_next_schedule(quality=5, repetitions=0, ease_factor=2.5, interval_days=0)
    state = compute_next_schedule(
        quality=5, repetitions=state.repetitions, ease_factor=state.ease_factor, interval_days=state.interval_days
    )
    state = compute_next_schedule(
        quality=5, repetitions=state.repetitions, ease_factor=state.ease_factor, interval_days=state.interval_days
    )
    # interval should now be roughly 6 * ease_factor (> 6 days, ease_factor grew past 2.5)
    assert state.repetitions == 3
    assert state.interval_days == round(6 * 2.7)


def test_failed_recall_resets_repetitions_and_schedules_tomorrow():
    # Build up some progress first...
    state = compute_next_schedule(quality=5, repetitions=0, ease_factor=2.5, interval_days=0)
    state = compute_next_schedule(
        quality=5, repetitions=state.repetitions, ease_factor=state.ease_factor, interval_days=state.interval_days
    )
    assert state.repetitions == 2

    # ...then fail a review.
    failed = compute_next_schedule(
        quality=1, repetitions=state.repetitions, ease_factor=state.ease_factor, interval_days=state.interval_days
    )
    assert failed.repetitions == 0
    assert failed.interval_days == 1


def test_poor_recall_lowers_ease_factor():
    outcome = compute_next_schedule(
        quality=0, repetitions=0, ease_factor=DEFAULT_EASE_FACTOR, interval_days=0
    )
    assert outcome.ease_factor < DEFAULT_EASE_FACTOR


def test_ease_factor_never_drops_below_minimum():
    ease = DEFAULT_EASE_FACTOR
    repetitions = 0
    interval = 0
    # repeatedly fail -- ease factor should floor out, never go negative or below 1.3
    for _ in range(20):
        outcome = compute_next_schedule(
            quality=0, repetitions=repetitions, ease_factor=ease, interval_days=interval
        )
        ease, repetitions, interval = outcome.ease_factor, outcome.repetitions, outcome.interval_days
    assert ease >= 1.3


def test_quality_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        compute_next_schedule(quality=6, repetitions=0, ease_factor=2.5, interval_days=0)
    with pytest.raises(ValueError):
        compute_next_schedule(quality=-1, repetitions=0, ease_factor=2.5, interval_days=0)


# --- Endpoint integration tests ---


def _auth_headers(client, username="learner", email="learner@example.com", password="password1234"):
    client.post("/auth/register", json={"username": username, "email": email, "password": password})
    login = client.post("/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_review_queue_requires_auth(client):
    response = client.get("/users/me/review-queue")
    assert response.status_code == 401


def test_review_queue_contains_new_words_before_any_review(client):
    headers = _auth_headers(client)
    response = client.get("/users/me/review-queue", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2  # the two seeded vocabulary words
    assert all(item["is_new"] for item in items)
    assert all(item["language_code"] == "es" for item in items)


def test_submit_review_updates_schedule(client):
    headers = _auth_headers(client)
    response = client.post(
        "/vocabulary/1/review", json={"quality": 5}, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["repetitions"] == 1
    assert data["interval_days"] == 1


def test_reviewed_word_leaves_queue_until_due_again(client):
    headers = _auth_headers(client)
    client.post("/vocabulary/1/review", json={"quality": 5}, headers=headers)

    response = client.get("/users/me/review-queue", headers=headers)
    items = response.json()
    ids = [item["vocabulary_item_id"] for item in items]
    # word 1 was just scheduled a day out, so it shouldn't be due again today
    assert 1 not in ids
    assert 2 in ids  # the other word is still new/untouched


def test_submit_review_missing_vocabulary_item_returns_404(client):
    headers = _auth_headers(client)
    response = client.post("/vocabulary/999/review", json={"quality": 5}, headers=headers)
    assert response.status_code == 404


def test_submit_review_rejects_out_of_range_quality(client):
    headers = _auth_headers(client)
    response = client.post("/vocabulary/1/review", json={"quality": 9}, headers=headers)
    assert response.status_code == 422
