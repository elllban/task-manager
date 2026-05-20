import time
import httpx

_ts = int(time.time() * 1000)


class TestAuthAPI:
    def test_register(self, client: httpx.Client):
        response = client.post("/api/v1/auth/register", json={
            "email": f"test_new_{_ts}@test.com",
            "password": "Password1!",
            "password_confirm": "Password1!",
            "name": "New User",
        })
        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_duplicate(self, client: httpx.Client):
        email = f"test_dup_{_ts}@test.com"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password1!",
            "password_confirm": "Password1!",
        })
        response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password1!",
            "password_confirm": "Password1!",
        })
        assert response.status_code == 400
        assert "already registered" in response.text

    def test_login(self, client: httpx.Client):
        email = f"test_login_{_ts}@test.com"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password1!",
            "password_confirm": "Password1!",
        })
        response = client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "Password1!",
        })
        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data

    def test_login_invalid(self, client: httpx.Client):
        response = client.post("/api/v1/auth/login", data={
            "username": f"noone_{_ts}@test.com",
            "password": "wrong",
        })
        assert response.status_code == 401

    def test_me(self, client: httpx.Client):
        email = f"test_me_{_ts}@test.com"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password1!",
            "password_confirm": "Password1!",
        })
        login_resp = client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "Password1!",
        })
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]

        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert response.json()["email"] == email

    def test_unauthorized(self, client: httpx.Client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
