from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db import create_db_and_tables
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application is starting up...")
    create_db_and_tables()
    yield
    logger.info("Application is shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok"}
