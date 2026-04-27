"""FastAPI application entry: CORS, logging, lifespan, and router registration."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import experiments, ingest, pdf, ping, query, status
from config import settings
from index_state import describe_index_paths, indexes_exist
from indexing import IndexManager
from retrieval.retriever import Retriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Configure application state at startup.

    Loads serialized indexes at startup when present (performance rule).
    """
    app.state.indexed = indexes_exist()
    if app.state.indexed:
        logger.info(
            "Index artifacts found: %s",
            describe_index_paths(),
        )
        try:
            mgr = IndexManager()
            mgr.load_all()
            app.state.index_manager = mgr
            app.state.retriever = Retriever(mgr)
            logger.info("Index objects loaded into memory at startup.")
        except Exception:
            logger.exception("Index objects found but could not be loaded.")
    else:
        logger.info("No complete index set on disk yet (expected before Phase 2).")
    yield


app = FastAPI(
    title="Academic Policy QA API",
    lifespan=lifespan,
)

# Deployment CORS configuration
origins = settings.CORS_ALLOWED_ORIGINS
origin_regex = settings.CORS_ALLOWED_ORIGIN_REGEX

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ping.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(status.router)
app.include_router(experiments.router)
app.include_router(pdf.router)
