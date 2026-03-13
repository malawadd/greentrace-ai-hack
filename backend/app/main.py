from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.router import api_router


app = FastAPI(
    title="GreenTrace Backend",
    description="FastAPI service for running the GreenTrace Apify actor",
    version="1.0.0",
)
app.include_router(api_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "FastAPI service is running",
        "mountedAt": "/svc/api",
        "docs": "/svc/api/docs",
    }


@app.get("/status")
def get_status() -> dict[str, str]:
    return {
        "service": "backend",
        "framework": "fastapi",
        "mountedAt": "/svc/api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }