import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.api.crud_routes import (
    test_sets_router, rubrics_router, experiments_db_router,
    runs_router, settings_router, ALLOWED_SETTINGS,
)
from src.db.engine import create_tables, SessionLocal
from src.db import crud


def _load_settings_to_env():
    db = SessionLocal()
    try:
        for key in ALLOWED_SETTINGS:
            setting = crud.get_setting(db, key)
            if setting and key not in os.environ:
                os.environ[key] = setting.value
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    _load_settings_to_env()
    yield


app = FastAPI(title="Prompt A/B Testing API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(test_sets_router)
app.include_router(rubrics_router)
app.include_router(experiments_db_router)
app.include_router(runs_router)
app.include_router(settings_router)
