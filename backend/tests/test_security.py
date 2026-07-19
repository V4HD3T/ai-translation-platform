import re

from app.services.email_service import get_email_service


def _register_and_login(client, username="secuser", email="secuser@example.com", password="password1234"):
    client.post("/auth/register", json={"username": username, "email": email, "password": password})
    login = client.post("/auth/login", data={"username": username, "password": password})
    return login.json()


# --- Rate limiting ---


def test_login_rate_limited_after_too_many_attempts(client):
    client.post(
        "/auth/register",
        json={"username": "ratelimited", "email": "ratelimited@example.com", "password": "correct-password"},
    )
    for _ in range(5):
        response = client.post(
            "/auth/login", data={"username": "ratelimited", "password": "wrong-password"}
        )
        assert response.status_code == 401

    sixth = client.post("/auth/login", data={"username": "ratelimited", "password": "wrong-password"})
    assert sixth.status_code == 429


def test_successful_login_resets_rate_limit(client):
    client.post(
        "/auth/register",
        json={"username": "retryok", "email": "retryok@example.com", "password": "correct-password"},
    )
    for _ in range(4):
        client.post("/auth/login", data={"username": "retryok", "password": "wrong-password"})

    success = client.post("/auth/login", data={"username": "retryok", "password": "correct-password"})
    assert success.status_code == 200

    # the failed attempts before the success shouldn't count against the
    # limit anymore
    again = client.post("/auth/login", data={"username": "retryok", "password": "correct-password"})
    assert again.status_code == 200


def test_register_rate_limited_after_too_many_attempts(client):
    for i in range(5):
        client.post(
            "/auth/register",
            json={"username": f"burst{i}", "email": f"burst{i}@example.com", "password": "password1234"},
        )
    sixth = client.post(
        "/auth/register",
        json={"username": "burst5", "email": "burst5@example.com", "password": "password1234"},
    )
    assert sixth.status_code == 429


# --- Refresh tokens ---


def test_login_returns_refresh_token(client):
    tokens = _register_and_login(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["refresh_token"] != tokens["access_token"]


def test_refresh_returns_a_working_new_access_token(client):
    tokens = _register_and_login(client, username="refresher", email="refresher@example.com")
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_access_token = response.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me.status_code == 200


def test_refresh_with_garbage_token_fails(client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_refresh_rotates_token_old_one_stops_working(client):
    tokens = _register_and_login(client, username="rotator", email="rotator@example.com")
    old_refresh = tokens["refresh_token"]

    first_refresh = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert first_refresh.status_code == 200

    # the old refresh token was single-use; using it again should fail
    # (and per the reuse-detection below, revokes everything)
    second_attempt = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert second_attempt.status_code == 401


def test_reusing_revoked_refresh_token_kills_all_sessions(client):
    tokens = _register_and_login(client, username="thief-target", email="thieftarget@example.com")
    old_refresh = tokens["refresh_token"]

    rotated = client.post("/auth/refresh", json={"refresh_token": old_refresh}).json()
    new_refresh = rotated["refresh_token"]

    # replay the OLD (now-revoked) refresh token, simulating a stolen token
    # being used after the legitimate client already rotated past it
    client.post("/auth/refresh", json={"refresh_token": old_refresh})

    # the legitimate, rotated token should now ALSO be dead as a precaution
    response = client.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    tokens = _register_and_login(client, username="loggerouter", email="loggerouter@example.com")
    logout = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout.status_code == 200

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_logout_all_revokes_every_session(client):
    tokens_a = _register_and_login(client, username="multisession", email="multisession@example.com")
    login2 = client.post("/auth/login", data={"username": "multisession", "password": "password1234"})
    tokens_b = login2.json()

    headers = {"Authorization": f"Bearer {tokens_a['access_token']}"}
    response = client.post("/auth/logout-all", headers=headers)
    assert response.status_code == 200

    refresh_a = client.post("/auth/refresh", json={"refresh_token": tokens_a["refresh_token"]})
    refresh_b = client.post("/auth/refresh", json={"refresh_token": tokens_b["refresh_token"]})
    assert refresh_a.status_code == 401
    assert refresh_b.status_code == 401


# --- Email verification ---


def test_new_user_is_not_verified_by_default(client):
    tokens = _register_and_login(client, username="unverified", email="unverified@example.com")
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.json()["is_verified"] is False


def test_register_sends_verification_email(client):
    client.post(
        "/auth/register",
        json={"username": "emailcheck", "email": "emailcheck@example.com", "password": "password1234"},
    )
    sent = get_email_service().sent_emails
    assert len(sent) == 1
    assert sent[0].to == "emailcheck@example.com"
    assert "verify-email?token=" in sent[0].body


def test_verify_email_with_token_from_sent_email(client):
    client.post(
        "/auth/register",
        json={"username": "verifyme", "email": "verifyme@example.com", "password": "password1234"},
    )
    sent = get_email_service().sent_emails
    token = re.search(r"token=([\w-]+)", sent[0].body).group(1)

    response = client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 200

    login = client.post("/auth/login", data={"username": "verifyme", "password": "password1234"})
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.json()["is_verified"] is True


def test_verify_email_with_invalid_token_fails(client):
    response = client.post("/auth/verify-email", json={"token": "not-a-real-token"})
    assert response.status_code == 400


def test_verify_email_token_is_single_use(client):
    client.post(
        "/auth/register",
        json={"username": "onceonly", "email": "onceonly@example.com", "password": "password1234"},
    )
    token = re.search(r"token=([\w-]+)", get_email_service().sent_emails[0].body).group(1)

    first = client.post("/auth/verify-email", json={"token": token})
    assert first.status_code == 200
    second = client.post("/auth/verify-email", json={"token": token})
    assert second.status_code == 400


# --- Password reset ---


def test_request_password_reset_sends_email(client):
    client.post(
        "/auth/register",
        json={"username": "forgetful", "email": "forgetful@example.com", "password": "old-password1"},
    )
    get_email_service().sent_emails.clear()  # discard the verification email from registration

    response = client.post("/auth/request-password-reset", json={"email": "forgetful@example.com"})
    assert response.status_code == 200
    sent = get_email_service().sent_emails
    assert len(sent) == 1
    assert "reset-password?token=" in sent[0].body


def test_request_password_reset_for_unknown_email_gives_generic_response(client):
    # Same response either way -- revealing whether an email is registered
    # would let an attacker enumerate accounts.
    known = client.post(
        "/auth/register",
        json={"username": "known", "email": "known@example.com", "password": "password1234"},
    )
    known_response = client.post("/auth/request-password-reset", json={"email": "known@example.com"})
    unknown_response = client.post(
        "/auth/request-password-reset", json={"email": "nobody-here@example.com"}
    )
    assert known.status_code == 201
    assert known_response.status_code == unknown_response.status_code == 200
    assert known_response.json() == unknown_response.json()


def test_reset_password_with_valid_token_changes_password(client):
    client.post(
        "/auth/register",
        json={"username": "resetme", "email": "resetme@example.com", "password": "old-password1"},
    )
    get_email_service().sent_emails.clear()
    client.post("/auth/request-password-reset", json={"email": "resetme@example.com"})
    token = re.search(r"token=([\w-]+)", get_email_service().sent_emails[0].body).group(1)

    reset = client.post(
        "/auth/reset-password", json={"token": token, "new_password": "brand-new-password1"}
    )
    assert reset.status_code == 200

    old_login = client.post("/auth/login", data={"username": "resetme", "password": "old-password1"})
    assert old_login.status_code == 401

    new_login = client.post(
        "/auth/login", data={"username": "resetme", "password": "brand-new-password1"}
    )
    assert new_login.status_code == 200


def test_reset_password_revokes_existing_sessions(client):
    tokens = _register_and_login(client, username="sessionkiller", email="sessionkiller@example.com")
    get_email_service().sent_emails.clear()
    client.post("/auth/request-password-reset", json={"email": "sessionkiller@example.com"})
    token = re.search(r"token=([\w-]+)", get_email_service().sent_emails[0].body).group(1)

    client.post("/auth/reset-password", json={"token": token, "new_password": "another-new-password1"})

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_reset_password_with_invalid_token_fails(client):
    response = client.post(
        "/auth/reset-password", json={"token": "not-a-real-token", "new_password": "whatever12"}
    )
    assert response.status_code == 400


# --- Security headers ---


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert "max-age" in response.headers["strict-transport-security"]


# --- Optional-auth endpoints: invalid tokens must 401, not silently downgrade ---


def test_optional_auth_endpoint_rejects_invalid_token(client):
    # A *present but invalid* token is a 401, not a silent anonymous
    # downgrade. The frontend attaches its access token to these endpoints
    # and only knows to refresh the session when it sees a 401 -- silently
    # serving an anonymous 200 meant expired sessions kept "working" while
    # history saving and adaptive difficulty quietly switched off.
    response = client.post(
        "/translate",
        headers={"Authorization": "Bearer not-a-real-token"},
        json={"text": "hello there", "source_lang": "en", "target_lang": "es"},
    )
    assert response.status_code == 401


def test_optional_auth_endpoint_rejects_expired_token(client):
    from app.security import create_access_token

    _register_and_login(client, username="expiredsess", email="expiredsess@example.com")
    expired = create_access_token(subject="1", expires_minutes=-1)
    response = client.post(
        "/translate",
        headers={"Authorization": f"Bearer {expired}"},
        json={"text": "hello there", "source_lang": "en", "target_lang": "es"},
    )
    assert response.status_code == 401


def test_access_token_with_non_numeric_subject_is_rejected_cleanly(client):
    # A signed token whose `sub` isn't a well-formed user id should be a
    # clean 401, not an unhandled int() ValueError turning into a 500.
    from app.security import create_access_token

    weird = create_access_token(subject="definitely-not-a-user-id")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {weird}"})
    assert response.status_code == 401


# --- v0.0.8: app-wide + /translate rate limiting ---


def test_translate_endpoint_is_rate_limited(client, monkeypatch):
    from app.services.rate_limiter import translate_rate_limiter

    monkeypatch.setattr(translate_rate_limiter, "max_attempts", 3)
    payload = {"text": "hello", "source_lang": "en", "target_lang": "es"}
    for _ in range(3):
        assert client.post("/translate", json=payload).status_code == 200
    blocked = client.post("/translate", json=payload)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_general_api_rate_limit_backstop(client, monkeypatch):
    from app.services.rate_limiter import api_rate_limiter

    monkeypatch.setattr(api_rate_limiter, "max_attempts", 5)
    for _ in range(5):
        assert client.get("/languages").status_code == 200
    blocked = client.get("/languages")
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_health_endpoint_is_exempt_from_general_rate_limit(client, monkeypatch):
    # Deployment platforms poll /health constantly; it must never 429.
    from app.services.rate_limiter import api_rate_limiter

    monkeypatch.setattr(api_rate_limiter, "max_attempts", 1)
    for _ in range(5):
        assert client.get("/health").status_code == 200


def test_auth_rate_limit_response_includes_retry_after(client):
    for _ in range(5):
        client.post("/auth/login", data={"username": "ghost", "password": "wrong-password"})
    blocked = client.post("/auth/login", data={"username": "ghost", "password": "wrong-password"})
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
