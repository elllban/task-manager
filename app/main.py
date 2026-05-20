from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.middleware import IdempotencyMiddleware
from app.api.v1 import attachments, auth, categories, projects, tasks, users
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title='Task Manager API', version='1.0.0', lifespan=lifespan, docs_url='/api/docs', redoc_url='/api/redoc'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(IdempotencyMiddleware)

app.mount('/uploads', StaticFiles(directory='uploads'), name='uploads')

app.include_router(auth.router, prefix='/api/v1')
app.include_router(users.router, prefix='/api/v1')
app.include_router(categories.router, prefix='/api/v1')
app.include_router(projects.router, prefix='/api/v1')
app.include_router(tasks.router, prefix='/api/v1')
app.include_router(attachments.router, prefix='/api/v1')


@app.get('/')
async def root():
    return {
        'message': 'Task Manager API',
        'docs': '/api/docs',
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
