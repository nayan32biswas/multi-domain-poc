from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import DEBUG, LOCAL_SUBDOMAIN
from app.services import get_project_by_subdomain


def get_host_from_request(request: Request) -> str:
    forwarded_host = request.headers.get("x-forwarded-host", "")
    if forwarded_host:
        return forwarded_host.split(":")[0].lower()

    return request.headers.get("host", "").split(":")[0].lower()


def get_subdomain_from_host(host: str) -> str | None:
    if DEBUG is True and (host.startswith("localhost") or host.startswith("127.0.0.1")):
        return LOCAL_SUBDOMAIN

    parts = host.split(".")
    if len(parts) < 3:
        return None

    subdomain = parts[0]

    return subdomain


async def domain_middleware_utils(request: Request, call_next: Any) -> Any:
    host = get_host_from_request(request)
    subdomain = get_subdomain_from_host(host)
    if not subdomain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subdomain not found",
        )

    project = get_project_by_subdomain(subdomain)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Project not found for the given host: {host}"},
        )

    request.state.project = project
    request.state.host = host

    response = await call_next(request)

    return response
