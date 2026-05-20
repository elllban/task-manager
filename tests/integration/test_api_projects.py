import time
import httpx

_ts = int(time.time() * 1000)


class TestProjectsAPI:
    def _register(self, client: httpx.Client, tag: str) -> str:
        email = f"proj_{tag}_{_ts}@test.com"
        resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password1!",
            "password_confirm": "Password1!",
        })
        assert resp.status_code == 200, resp.text
        return resp.json()["access_token"]

    def _create_category(self, client: httpx.Client, token: str, tag: str) -> int:
        resp = client.post("/api/v1/categories/", json={
            "name": f"Cat {tag} {_ts}",
            "color": "#00FF00",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        return resp.json()["id"]

    def test_create_project(self, client: httpx.Client):
        token = self._register(client, "create")
        cat_id = self._create_category(client, token, "create")
        response = client.post("/api/v1/projects/", json={
            "name": f"My Project {_ts}",
            "category_id": cat_id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, response.text
        assert response.json()["name"] == f"My Project {_ts}"

    def test_get_projects_paginated(self, client: httpx.Client):
        token = self._register(client, "list")
        cat_id = self._create_category(client, token, "list")
        for i in range(3):
            client.post("/api/v1/projects/", json={
                "name": f"Project {i} {_ts}",
                "category_id": cat_id,
            }, headers={"Authorization": f"Bearer {token}"})

        response = client.get(
            "/api/v1/projects/?page=1&size=2",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["total"] >= 3

    def test_get_project_by_id(self, client: httpx.Client):
        token = self._register(client, "get")
        cat_id = self._create_category(client, token, "get")
        create_resp = client.post("/api/v1/projects/", json={
            "name": f"Specific Proj {_ts}",
            "category_id": cat_id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert create_resp.status_code == 200, create_resp.text
        proj_id = create_resp.json()["id"]

        response = client.get(
            f"/api/v1/projects/{proj_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == f"Specific Proj {_ts}"

    def test_project_members(self, client: httpx.Client):
        owner_token = self._register(client, "owner")
        cat_id = self._create_category(client, owner_token, "members")
        create_resp = client.post("/api/v1/projects/", json={
            "name": f"Team Proj {_ts}",
            "category_id": cat_id,
        }, headers={"Authorization": f"Bearer {owner_token}"})
        assert create_resp.status_code == 200, create_resp.text
        proj_id = create_resp.json()["id"]

        member_token = self._register(client, "member")
        email = f"proj_member_{_ts}@test.com"
        member_resp = client.get(
            "/api/v1/users/?page=1&size=100",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert member_resp.status_code == 200, member_resp.text
        users = [u for u in member_resp.json()["items"] if u["email"] == email]
        assert len(users) == 1, f"Member {email} not found in users list"
        member_id = users[0]["id"]

        add_resp = client.post(
            f"/api/v1/projects/{proj_id}/members",
            json={"user_id": member_id, "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert add_resp.status_code == 200, add_resp.text

        members_resp = client.get(
            f"/api/v1/projects/{proj_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert members_resp.status_code == 200
        assert members_resp.json()["total"] >= 2
