"""Package REST API."""
import os
from typing import Dict

from fastapi import FastAPI
from mangum import Mangum
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.cors import CORSMiddleware

from sentiment_flanders.api.routers import (
    impressions_daily,
    impressions_hourly,
    impressions_monthly,
)

app = FastAPI(
        title="Sentiment Flanders",
        description="Visualisations of the global sentiment of the Flemish population",
)

# Add routers.
app.include_router(impressions_hourly.router, prefix="/api/v1/impressions/hourly")
app.include_router(impressions_daily.router, prefix="/api/v1/impressions/daily")
app.include_router(impressions_monthly.router, prefix="/api/v1/impressions/monthly")

# Add middleware.
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)
app.add_middleware(SentryAsgiMiddleware)
api_handler = Mangum(app) if os.environ.get("AWS_EXECUTION_ENV") else None


# Add routes that are not managed by routers.
@app.get("/")
def root() -> Dict[str, str]:
    """Get demo."""
    return {"message": "Hello World"}

# TODO: Prefer HTTPException without handle, currently nothing must be handled
# # Add exception handlers.
# @app.exception_handler(StarletteHTTPException)
# def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
#     """Handle generic HTTP exceptions."""
#     return JSONResponse(content=jsonable_encoder({"detail": str(exc)}))
#
#
# @app.exception_handler(RequestValidationError)
# def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
#     """Handle request validation errors."""
#     return JSONResponse(content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}))
