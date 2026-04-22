import uvicorn
from fastapi import FastAPI

from .routes import router

app = FastAPI(
    title="Flight Planner API",
    description="Mock flight data API for the agentic flight planner sandbox.",
    version="0.1.0",
)

app.include_router(router)


def start() -> None:
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
