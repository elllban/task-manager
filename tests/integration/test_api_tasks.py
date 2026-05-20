import time
import httpx

_ts = int(time.time() * 1000)


class TestTasksAPI:
    def _register(self, client: httpx.Client, tag: str) -> str:
        email = f"task_{tag}_{_ts}@test.com"
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
            "color": "#FF0000",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        return resp.json()["id"]

    def _create_project(self, client: httpx.Client, token: str, cat_id: int) -> int:
        resp = client.post("/api/v1/projects/", json={
            "name": f"Proj {_ts}",
            "category_id": cat_id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        return resp.json()["id"]

    def test_create_task(self, client: httpx.Client):
        token = self._register(client, "create")
        cat_id = self._create_category(client, token, "create")
        proj_id = self._create_project(client, token, cat_id)

        response = client.post("/api/v1/tasks/", json={
            "title": f"Test Task {_ts}",
            "project_id": proj_id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["title"] == f"Test Task {_ts}"
        assert data["project_id"] == proj_id

    def test_get_tasks_paginated(self, client: httpx.Client):
        token = self._register(client, "list")
        cat_id = self._create_category(client, token, "list")
        proj_id = self._create_project(client, token, cat_id)

        for i in range(3):
            client.post("/api/v1/tasks/", json={
                "title": f"Task {i} {_ts}",
                "project_id": proj_id,
            }, headers={"Authorization": f"Bearer {token}"})

        response = client.get(
            "/api/v1/tasks/?page=1&size=2",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["total"] >= 3
        assert len(data["items"]) == 2

    def test_get_task_by_id(self, client: httpx.Client):
        token = self._register(client, "get")
        cat_id = self._create_category(client, token, "get")
        proj_id = self._create_project(client, token, cat_id)

        create_resp = client.post("/api/v1/tasks/", json={
            "title": f"Specific Task {_ts}",
            "project_id": proj_id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert create_resp.status_code == 200, create_resp.text
        task_id = create_resp.json()["id"]

        response = client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == f"Specific Task {_ts}"

    def test_update_task(self, client: httpx.Client):
        token = self._register(client, "upd")
        cat_id = self._create_category(client, token, "upd")
        proj_id = self._create_project(client, token, cat_id)

        create_resp = client.post("/api/v1/tasks/", json={
            "title": f"Old Title {_ts}",
            "project_id": proj_id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert create_resp.status_code == 200, create_resp.text
        task_id = create_resp.json()["id"]

        response = client.put(
            f"/api/v1/tasks/{task_id}",
            json={"title": f"New Title {_ts}"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        assert response.json()["title"] == f"New Title {_ts}"

    def test_delete_task(self, client: httpx.Client):
        token = self._register(client, "del")
        cat_id = self._create_category(client, token, "del")
        proj_id = self._create_project(client, token, cat_id)

        create_resp = client.post("/api/v1/tasks/", json={
            "title": f"To Delete {_ts}",
            "project_id": proj_id,
        }, headers={"Authorization": f"Bearer {token}"})
        assert create_resp.status_code == 200, create_resp.text
        task_id = create_resp.json()["id"]

        response = client.delete(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in (200, 204), response.text
