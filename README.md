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
2. Start PostgreSQL via Docker: `docker-compose up -d`
3. Run database setup: `python setup_db.py`
4. Start the app: `uvicorn app.main:app --reload`

## API Documentation

After starting the app, visit `/api/docs` for Swagger UI.
