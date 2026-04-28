from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import CORS_ORIGINS
from app.db.session import Base, SessionLocal, engine
from app.models import entities  # noqa: F401
from app.services.auth import seed_demo_users


def create_app() -> FastAPI:
    app = FastAPI(
        title="Analyse RH API",
        version="1.0.0",
        description="API de gestion et d'analyse des données RH.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()
