from typing import Any

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from mongodb_odm import connect, disconnect

from app import config, routers


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    connect(config.DB_URL)

    yield

    disconnect()


app: Any = FastAPI(debug=config.DEBUG, lifespan=lifespan)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes BEFORE static file serving
app.include_router(routers.router, tags=["base"])


if __name__ == "__main__":
    print("Starting FastAPI server...")
