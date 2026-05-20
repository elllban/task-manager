# Task Manager API

FastAPI-based task management system with user authentication, project management, task assignment, and file attachments.

## Features

- User registration and authentication (JWT)
- Project and category management
- Task creation with priorities and subtasks
- File attachments
- Calendar view for tasks
- Email password reset

## Setup

1. Create `.env` file based on `.env.example`
2. Start everything: `docker-compose up -d --build`
3. App is at `http://localhost:8000`

### Local dev (without Docker)

1. Start PostgreSQL: `docker-compose up -d postgres`
2. Install deps: `pip install -r requirements.txt`
3. Run migrations: `alembic upgrade head`
4. Start the app: `uvicorn app.main:app --reload`

## API Documentation

After starting the app, visit `/api/docs` for Swagger UI.
