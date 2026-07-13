import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.assignments.router import router as assignments_router
from app.auth.router import router as auth_router
from app.content.router import router as content_router
from app.core.config import settings
from app.core.embedding import load_embedding_model
from app.core.errors import register_exception_handlers
from app.dashboard.router import router as dashboard_router
from app.progress.router import router as progress_router
from app.progress.my_assignments import router as my_assignments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(load_embedding_model)
    yield


app = FastAPI(title="TalentPilot-AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(assignments_router, prefix="/api/assignments", tags=["assignments"])
app.include_router(my_assignments_router, prefix="/api")
app.include_router(content_router, prefix="/api/content", tags=["content"])
app.include_router(progress_router, tags=["progress"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/")
async def root() -> dict:
    return {"status": "ok"}
