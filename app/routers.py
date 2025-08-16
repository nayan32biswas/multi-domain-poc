import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.config import DEBUG, LOCAL_SUBDOMAIN, SITE_DOMAIN
from app.models import Project
from app.schemas import (
    CustomDomainIn,
    DomainVerificationOut,
    ProjectIn,
    ProjectOut,
)
from app.services import (
    generate_subdomain,
    get_domain_verification_instructions,
    get_project_or_404,
    get_sanitized_custom_domain,
    get_verification_record_name,
    is_customdomain_available,
    remove_custom_domain,
    set_custom_domain,
    verify_custom_domain,
)
from app.utils import update_partially

router = APIRouter(prefix="/api")


def get_subdomain_from_request(request: Request) -> str | None:
    subdomain = request.headers.get("X-Subdomain")
    if DEBUG is True and subdomain == LOCAL_SUBDOMAIN:
        return LOCAL_SUBDOMAIN
    if not subdomain:
        return None

    return subdomain.lower()


def get_custom_domain_from_request(request: Request) -> str | None:
    custom_domain = request.headers.get("X-Custom-Domain")
    if DEBUG is True and custom_domain == LOCAL_SUBDOMAIN:
        return LOCAL_SUBDOMAIN
    if not custom_domain:
        return None

    return custom_domain.lower()


@router.get("/projects")
def get_projects(
    subdomain: str | None = Depends(get_subdomain_from_request),
    custom_domain: None | str = Depends(get_custom_domain_from_request),
) -> Any:
    filter: dict[str, str] = {}
    if subdomain:
        filter["subdomain"] = subdomain
    elif custom_domain:
        filter["custom_domain"] = custom_domain

    query = Project.find(filter)

    projects = [ProjectOut(**project.model_dump()) for project in query]

    return {"results": projects}


@router.post("/projects")
def create_project(project_data: ProjectIn):
    project_dict = project_data.model_dump()

    subdomain = generate_subdomain()

    project_dict["subdomain"] = subdomain

    new_project = Project(**project_dict)
    new_project.is_active = True
    new_project.create()

    return ProjectOut(**new_project.model_dump())


@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    subdomain: str = Depends(get_subdomain_from_request),
    custom_domain: str = Depends(get_custom_domain_from_request),
):
    project = get_project_or_404(project_id, subdomain, custom_domain)

    return ProjectOut(**project.model_dump())


@router.put("/projects/{project_id}")
def update_project(
    project_data: ProjectIn,
    project_id: str,
):
    existing_project = get_project_or_404(project_id)

    existing_project = update_partially(existing_project, project_data)
    existing_project.update()

    return ProjectOut(**existing_project.model_dump())


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    subdomain: str = Depends(get_subdomain_from_request),
    custom_domain: str = Depends(get_custom_domain_from_request),
):
    project = get_project_or_404(project_id, subdomain, custom_domain)

    project.delete()

    return {"detail": "Project deleted successfully"}


instruction_template = """
Add a TXT record to your DNS:
Name: {verification_record_name}
Value: {verification_token}
"""


@router.post("/projects/{project_id}/custom-domain")
def add_custom_domain(
    project_id: str,
    domain_data: CustomDomainIn,
) -> DomainVerificationOut:
    project = get_project_or_404(project_id)

    custom_domain = get_sanitized_custom_domain(domain_data.custom_domain)
    if not custom_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom domain is not valid",
        )

    if not is_customdomain_available(custom_domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Custom domain '{custom_domain}' is already taken.",
        )

    updated_project = set_custom_domain(project, custom_domain)

    # Return verification instructions
    verification_record_name = get_verification_record_name(custom_domain)
    verification_token = updated_project.domain_verification_token

    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate verification token",
        )

    instruction_data = instruction_template.format(
        verification_record_name=verification_record_name,
        verification_token=verification_token,
    )
    return DomainVerificationOut(
        verification_token=verification_token,
        verification_record_name=verification_record_name,
        verification_record_value=verification_token,
        instructions=instruction_data,
    )


@router.post("/projects/{project_id}/verify-domain")
def verify_domain(project_id: str) -> dict[str, Any]:
    """Verify the custom domain for a project"""
    project = get_project_or_404(project_id)

    custom_domain = project.custom_domain
    if not custom_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain found for this project",
        )

    is_verified = verify_custom_domain(project)
    if is_verified:
        return {
            "verified": True,
            "message": f"Domain {project.custom_domain} has been successfully verified!",
            "domain": project.custom_domain,
            "configuration_message": "Domain configuration is valid.",
        }

    verification_token = project.domain_verification_token
    record_name = get_verification_record_name(custom_domain)

    return {
        "verified": False,
        "message": f"Domain {custom_domain} verification failed. Please check your DNS records.",
        "domain": custom_domain,
        "verification_token": verification_token,
        "record_name": record_name,
    }


@router.delete("/projects/{project_id}/custom-domain")
def remove_domain(project_id: str) -> dict[str, str]:
    """Remove custom domain from a project"""
    project = get_project_or_404(project_id)

    if not project.custom_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain associated with this project",
        )

    domain = project.custom_domain
    remove_custom_domain(project)

    return {"detail": f"Custom domain {domain} has been removed successfully"}


@router.get("/projects/{project_id}/custom-domain/instructions")
def get_domain_instructions(project_id: str) -> dict[str, Any]:
    """Get detailed instructions for domain verification"""
    project = get_project_or_404(project_id)

    if not project.subdomain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subdomain associated with this project",
        )

    if not project.custom_domain or not project.domain_verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain or verification token found for this project",
        )

    # Get detailed instructions
    instructions = get_domain_verification_instructions(
        domain=project.custom_domain,
        token=project.domain_verification_token,
        subdomain=project.subdomain,
    )

    return {
        "project_id": project_id,
        "project_title": project.title,
        "verification_status": "verified" if project.is_verified else "pending",
        **instructions,
    }


@router.get("/domain-check")
async def domain_check(domain: str | None = None) -> Any:
    """
    Check the validity of a domain.
    returning 200 OK if the domain is valid,
    403 Forbidden if the domain is not valid and reverse will not give access to the static files.

    You can create a separate service for this app
    to isolate the original API server on it's dedicated server.
    """

    logging.info(f"Checking domain: {domain}")

    if not domain:
        return Response(status_code=403)

    def get_subdomain_from_host(host: str) -> str | None:
        if not host.endswith(SITE_DOMAIN):
            return None

        parts = host.split(".")
        if len(parts) < 3:
            return None

        subdomain = parts[0]

        return subdomain

    def is_project_exists(filter: dict[str, Any]) -> bool:
        project = Project.find_one(filter)

        if project:
            return True

        return False

    def is_valid_subdomain(subdomain: str) -> bool:
        filter: dict[str, Any] = {
            "subdomain": subdomain,
            "is_active": True,
        }

        return is_project_exists(filter)

    def is_valid_domain(custom_domain: str) -> bool:
        filter: dict[str, Any] = {
            "is_active": True,
            "is_verified": True,
            "custom_domain": custom_domain,
        }

        return is_project_exists(filter)

    subdomain = get_subdomain_from_host(domain)

    if subdomain and is_valid_subdomain(subdomain):
        return Response(status_code=200)

    if is_valid_domain(domain):
        return Response(status_code=200)

    return Response(status_code=403)
