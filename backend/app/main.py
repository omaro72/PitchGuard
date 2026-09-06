from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.dependencies import ReviewApplicationServices, create_review_services
from app.api.routes import reviews_router
from app.config import Settings, get_settings


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["pitchguard-api"]


async def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service="pitchguard-api")


def create_app(
    settings: Settings | None = None,
    review_services_factory: Callable[
        [Settings], ReviewApplicationServices
    ] = create_review_services,
) -> FastAPI:
    resolved_settings = settings if settings is not None else get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        services = review_services_factory(resolved_settings)
        application.state.review_services = services
        try:
            yield
        finally:
            await services.provider.close()

    application = FastAPI(title="PitchGuard API", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.add_api_route(
        "/api/health",
        get_health,
        methods=["GET"],
        response_model=HealthResponse,
    )
    application.include_router(reviews_router, prefix="/api/v1")
    return application


app = create_app()
