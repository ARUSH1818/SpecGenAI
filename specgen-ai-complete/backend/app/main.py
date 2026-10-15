"""
SpecGen AI backend — Sprint 1 (auth) + Sprint 2 (idea submission, AI generation).

Run with:  uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth as auth_router
from .routers import projects as projects_router
from .routers import admin as admin_router

Base.metadata.create_all(bind=engine)  # creates specgen.db tables on first run

app = FastAPI(
    title="SpecGen AI",
    description="AI-assisted platform for generating software requirement specifications.",
    version="0.4.0",  # Sprint 4 increment
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(projects_router.router)
app.include_router(admin_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
