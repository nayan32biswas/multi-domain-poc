import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import DEBUG, LOCAL_SUBDOMAIN
from app.models import Project
from app.schemas import (
    CustomDomainIn,
    DomainVerificationOut,
    ProjectIn,
    ProjectOut,
)
from app.services import (
    get_domain_verification_instructions,
    get_project_or_404,
    get_sanitized_subdomain,
    get_verification_record_name,
    remove_custom_domain,
    set_custom_domain,
    verify_custom_domain,
)
from app.utils import update_partially

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


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
    if custom_domain:
        filter["custom_domain"] = custom_domain

    query = Project.find(filter)

    projects = [ProjectOut(**project.model_dump()) for project in query]

    return {"results": projects}


@router.post("/projects")
def create_project(project_data: ProjectIn):
    subdomain = get_sanitized_subdomain(project_data.subdomain)
    project_dict = project_data.model_dump()

    project_dict["subdomain"] = subdomain

    new_project = Project(**project_dict)
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
    subdomain: str = Depends(get_subdomain_from_request),
    custom_domain: str = Depends(get_custom_domain_from_request),
):
    existing_project = get_project_or_404(project_id, subdomain, custom_domain)

    existing_project = update_partially(existing_project, project_data)
    existing_project.subdomain = get_sanitized_subdomain(existing_project.subdomain)
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
    request: Request,
) -> DomainVerificationOut:
    project = get_project_or_404(project_id)

    updated_project = set_custom_domain(project, domain_data.custom_domain)

    # Return verification instructions
    verification_record_name = get_verification_record_name(domain_data.custom_domain)
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

    is_verified = verify_custom_domain(project)

    if is_verified:
        return {
            "verified": True,
            "message": f"Domain {project.custom_domain} has been successfully verified!",
            "domain": project.custom_domain,
        }

    custom_domain = project.custom_domain
    verification_token = project.domain_verification_token

    if not custom_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain found for this project",
        )

    return {
        "verified": False,
        "message": f"Domain {custom_domain} verification failed. Please check your DNS records.",
        "domain": custom_domain,
        "verification_token": verification_token,
        "record_name": get_verification_record_name(custom_domain),
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
