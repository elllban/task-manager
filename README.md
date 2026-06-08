# Task Manager API

FastAPI-based task management system with JWT authentication, project collaboration, task hierarchies, file attachments, and a calendar view.

## Tech Stack

- **Python 3.11+** / **FastAPI**
- **PostgreSQL** + **SQLAlchemy 2.0** (async)
- **Alembic** for migrations
- **JWT** (access + refresh tokens) with blacklisting
- **Ruff** for linting/formatting
- **pytest** + **httpx** for tests
- **Docker Compose** for local dev

## Features

### Auth
- Register / Login / Logout (JWT with refresh tokens)
- Forgot/reset password via email (SMTP)
- Change password
- JWT blacklisting on logout

### Users
- Profile CRUD
- Avatar upload
- Account deletion

### Projects
- Project CRUD with role-based access (owner / admin / member / viewer)
- Member management (add, remove members)
- Categorization via categories

### Categories
- CRUD for project categories (each with a name and color)

### Tasks
- Full CRUD with title, description, priority, due date
- Priorities: very urgent / urgent / can wait / not urgent
- Assignment to users
- Subtasks (tree hierarchy via `parent_id`)
- Mark as complete / uncomplete
- Filtering by project, priority, completion status
- Calendar view: task dates by month/year
- Assigned tasks view with stats
- Pagination on all list endpoints

### Attachments
- Upload / download / delete files per task
- Access control based on project membership

### Other
- CORS enabled
- Idempotency middleware
- Async session management
- Swagger UI at `/api/docs` and ReDoc at `/api/redoc`

## Quick Start

```bash
cp .env.example .env   # edit SMTP and SECRET_KEY
docker-compose up -d --build
```

App is at `http://localhost:8000` — docs at `/api/docs`.

### Local Dev (without Docker)

```bash
docker-compose up -d postgres          # start only DB
pip install -r requirements.txt        # install deps
alembic upgrade head                   # run migrations
uvicorn app.main:app --reload          # start dev server
```

## Makefile Commands

| Command | Description |
|---|---|
| `make dev` | Start dev server with hot reload |
| `make test` | Run all tests |
| `make test-unit` | Unit tests |
| `make test-integration` | Integration tests (spins up Docker) |
| `make test-cov` | Unit tests with coverage report |
| `make lint` | Run ruff linter |
| `make format` | Auto-format code with ruff |
| `make migrate` | Apply pending migrations |
| `make migrate-create msg="..."` | Create a new migration |
| `make docker-up` | Build and start all services |
| `make docker-down` | Stop services |

## Project Structure

```
app/
├── api/v1/          # Route handlers (auth, users, projects, tasks, categories, attachments)
├── core/            # Config, DB engine, security (JWT), cache
├── models/          # SQLAlchemy models (User, Project, Task, Category, Attachment)
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic layer
├── repositories/    # Data access layer
└── main.py          # FastAPI app entrypoint
```

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async DSN |
| `SECRET_KEY` | JWT signing key |
| `SMTP_HOST` / `SMTP_PORT` | SMTP server for emails |
| `SMTP_USER` / `SMTP_PASSWORD` | SMTP credentials |
| `SMTP_FROM` | Sender email address |

## API Endpoints

### Auth (`/api/v1/auth`)
`POST /register` · `POST /login` · `POST /refresh` · `POST /logout` · `GET /me` · `POST /forgot-password` · `POST /reset-password` · `POST /change-password`

### Users (`/api/v1/users`)
`GET /` · `GET /me` · `GET /{id}` · `PUT /me` · `POST /me/avatar` · `DELETE /me`

### Categories (`/api/v1/categories`)
`POST /` · `GET /` · `GET /{id}` · `PUT /{id}` · `DELETE /{id}`

### Projects (`/api/v1/projects`)
`POST /` · `GET /` · `GET /{id}` · `PUT /{id}` · `DELETE /{id}` · `POST /{id}/members` · `GET /{id}/members` · `DELETE /{id}/members/{user_id}` · `GET /category/{category_id}`

### Tasks (`/api/v1/tasks`)
`POST /` · `GET /` · `GET /assigned` · `GET /assigned/stats` · `GET /calendar/dates` · `GET /calendar` · `POST /calendar` · `GET /{id}` · `PUT /{id}` · `PATCH /{id}/complete` · `PATCH /{id}/uncomplete` · `DELETE /{id}` · `GET /project/{project_id}`

### Attachments (`/api/v1/attachments`)
`POST /tasks/{task_id}` · `GET /tasks/{task_id}` · `GET /{id}/download` · `DELETE /{id}`
