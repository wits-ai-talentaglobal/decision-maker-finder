from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import SessionLocal, init_models
from app.logging_conf import configure_logging
from app.routers import contacts, jobs, ws
from app.taxonomy import seed_default_taxonomy


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_models()
    async with SessionLocal() as session:
        await seed_default_taxonomy(session)
    yield


app = FastAPI(title="Decision-Maker Finder", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(contacts.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
