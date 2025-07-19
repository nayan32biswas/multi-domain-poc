from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_ROOT


def mount_static_files(app: FastAPI) -> None:
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


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
