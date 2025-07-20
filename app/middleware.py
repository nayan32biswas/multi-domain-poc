from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import API_SUBDOMAIN
from app.services import (
    get_project_by_custom_domain,
    get_project_by_subdomain,
    is_subdomain_format,
    is_valid_subdomain,
)


def get_host_from_request(request: Request) -> str:
    forwarded_host = request.headers.get("x-forwarded-host", "")
    if forwarded_host:
        return forwarded_host.split(":")[0].lower()

    return request.headers.get("host", "").split(":")[0].lower()


def get_subdomain_from_host(host: str) -> str | None:
    parts = host.split(".")
    if len(parts) < 3:
        return None

    subdomain = parts[0]

    return subdomain


async def domain_middleware_utils(request: Request, call_next: Any) -> Any:
    host = get_host_from_request(request)

    print(f"\nHost: {host}")

    # Determine if it's a subdomain or custom domain
    if is_subdomain_format(host):
        # Handle subdomain logic
        subdomain = get_subdomain_from_host(host)
        if not subdomain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subdomain not found",
            )

        print(f"Processing subdomain: {subdomain}")

        # For API subdomain, allow access without project lookup
        if subdomain == API_SUBDOMAIN:
            request.state.host = host
            request.state.subdomain = subdomain
            request.state.domain_type = "api_subdomain"
            request.state.project = None
        else:
            # Regular subdomain - lookup project
            if not is_valid_subdomain(subdomain):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": f"Project not found for subdomain: {subdomain}"},
                )

            project = get_project_by_subdomain(subdomain)
            if not project:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": f"Project not found for subdomain: {subdomain}"},
                )

            request.state.host = host
            request.state.subdomain = subdomain
            request.state.domain_type = "subdomain"
            request.state.project = project
    else:
        # Handle custom domain logic
        print(f"Processing custom domain: {host}")

        project = get_project_by_custom_domain(host)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Project not found for custom domain: {host}"},
            )

        # Check if domain is verified
        if not project.is_verified:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": f"Custom domain {host} is not verified. Please verify your domain first.",
                    "verification_required": True
                },
            )

        request.state.host = host
        request.state.subdomain = None
        request.state.domain_type = "custom_domain"
        request.state.project = project

    response = await call_next(request)

    return response
