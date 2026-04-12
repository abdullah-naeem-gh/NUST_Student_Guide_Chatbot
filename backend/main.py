"""FastAPI application entry: CORS, logging, lifespan, and router registration."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import ping
from config import settings
from index_state import describe_index_paths, indexes_exist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Configure application state at startup.

    Verifies whether serialized indexes exist; full loading is implemented in
    later phases when indexing modules are wired in.
    """
    app.state.indexed = indexes_exist()
    if app.state.indexed:
        logger.info(
            "Index artifacts found: %s",
            describe_index_paths(),
        )
        logger.info(
            "Index objects will be loaded when the indexing module is implemented."
        )
    else:
        logger.info("No complete index set on disk yet (expected before Phase 2).")
    yield


app = FastAPI(
    title="Academic Policy QA API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ping.router)
