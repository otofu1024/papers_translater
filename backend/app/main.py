from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.core.logging import setup_logging


setup_logging()
app = FastAPI(title="pdf-translate-local backend", version="0.1.0")
app.include_router(health_router)
app.include_router(jobs_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "pdf-translate-local backend"}
