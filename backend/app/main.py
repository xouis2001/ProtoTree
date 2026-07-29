import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.services.email_outbox import run_email_outbox_worker


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.database_url.startswith("sqlite"):
        await init_db()
    stop = asyncio.Event()
    worker = asyncio.create_task(run_email_outbox_worker(stop), name="email-outbox-worker")
    try:
        yield
    finally:
        stop.set()
        try:
            await asyncio.wait_for(worker, timeout=10)
        except TimeoutError:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)


app = FastAPI(title="ProtoTree API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "prototree-backend", "version": "0.1.0"}
