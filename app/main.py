from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app import config, routers
from app.middleware import domain_middleware_utils
from app.static_files import mount_static_files, serve_spa

app: Any = FastAPI(debug=config.DEBUG, lifespan=config.lifespan)

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
mount_static_files(app)


@app.middleware("http")
async def domain_middleware(request: Request, call_next: Any):
    return await domain_middleware_utils(request, call_next)


@app.get("/{full_path:path}")
async def serve_static(request: Request, full_path: str) -> Any:
    return await serve_spa(request, full_path)


if __name__ == "__main__":
    print("Starting FastAPI server...")
