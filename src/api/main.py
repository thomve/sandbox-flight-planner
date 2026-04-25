import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent_routes import router as agent_router
from .routes import router

app = FastAPI(
    title="Flight Planner API",
    description="Mock flight data API for the agentic flight planner sandbox.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(agent_router)


def start() -> None:
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
