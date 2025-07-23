import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from pymongo.database import Database

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = os.path.join(BASE_DIR, "static")


DEBUG = bool(os.environ.get("DEBUG", False))
DB_URL = str(os.environ.get("DB_URL"))

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*")
SITE_DOMAIN = str(os.environ.get("SITE_DOMAIN"))

LOCAL_SUBDOMAIN: str = "localhost"

db_client: MongoClient[Any] | None = None


def get_db_client() -> MongoClient[Any]:
    global db_client

    if not db_client:
        db_client = MongoClient(DB_URL)

    return db_client


def get_db() -> Database[Any]:
    return get_db_client().get_database()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    # Do some startup tasks
    pass

    yield  # This is where the app runs

    get_db_client().close()


app: Any = FastAPI(debug=DEBUG, lifespan=lifespan)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


class Utility:
    @staticmethod
    def get_host_from_request(request: Request) -> str:
        forwarded_host = request.headers.get("x-forwarded-host", "")
        if forwarded_host:
            return forwarded_host.split(":")[0].lower()
        return request.headers.get("host", "").split(":")[0].lower()

    @staticmethod
    def get_subdomain_from_host(host: str) -> str | None:
        if not host.endswith(SITE_DOMAIN):
            return None

        parts = host.split(".")
        if len(parts) < 3:
            return None

        subdomain = parts[0]

        return subdomain

    @staticmethod
    def is_project_exists(filter: dict[str, Any]) -> bool:
        db = get_db()
        for _ in db.project.find(filter, projection={"_id": 1}).limit(1):
            return True

        return False

    @staticmethod
    def is_valid_subdomain(subdomain: str) -> bool:
        filter: dict[str, Any] = {
            "subdomain": subdomain,
            "is_active": True,
        }

        return Utility.is_project_exists(filter)

    @staticmethod
    def is_valid_domain(custom_domain: str) -> bool:
        filter: dict[str, Any] = {
            "is_active": True,
            "is_verified": True,
            "custom_domain": custom_domain,
        }

        return Utility.is_project_exists(filter)


@app.middleware("http")
async def domain_middleware(request: Request, call_next: Any) -> Any:
    host = Utility.get_host_from_request(request)

    print(f"\nHost: {host}")

    if not host:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Host header is missing"},
        )

    subdomain = Utility.get_subdomain_from_host(host)

    if subdomain:
        if not Utility.is_valid_subdomain(subdomain):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Project not found for subdomain: {subdomain}"},
            )
    elif not Utility.is_valid_domain(host):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Project not found for custom domain: {host}"},
        )

    response = await call_next(request)
    return response


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str) -> Any:
    """Serve static files based on path, fallback to React SPA for non-API routes"""

    # Don't serve SPA for API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Construct the file path in the static directory
    static_file_path = Path(STATIC_ROOT) / full_path.lstrip("/")

    # Check if the specific file exists
    if static_file_path.exists() and static_file_path.is_file():
        return FileResponse(str(static_file_path))

    # Fall back to index.html for SPA routing
    return FileResponse(str(Path(STATIC_ROOT) / "index.html"))


if __name__ == "__main__":
    print("Starting FastAPI server...")
