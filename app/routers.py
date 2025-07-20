import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from mongodb_odm import ODMObjectId

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
        # Try to get from request state (set by middleware)
        return getattr(request.state, 'subdomain', None)

    return subdomain.lower()


def get_project_from_request(request: Request) -> Project | None:
    """Get project from request state (set by middleware)"""
    return getattr(request.state, 'project', None)


@router.get("/projects")
def get_projects(
    subdomain: str = Depends(get_subdomain_from_request),
    custom_domain: None | str = None,
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
    new_project = Project(**project_data.model_dump())
    new_project.create()

    return ProjectOut(**new_project.model_dump())


@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    subdomain: str = Depends(get_subdomain_from_request),
):
    project = get_project_or_404(subdomain, project_id)

    return ProjectOut(**project.model_dump())


@router.put("/projects/{project_id}")
def update_project(
    project_data: ProjectIn,
    project_id: str,
    subdomain: str = Depends(get_subdomain_from_request),
):
    existing_project = get_project_or_404(subdomain, project_id)

    existing_project = update_partially(existing_project, project_data)
    existing_project.update()

    return ProjectOut(**existing_project.model_dump())


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    subdomain: str = Depends(get_subdomain_from_request),
):
    project = get_project_or_404(subdomain, project_id)
    project.delete()

    return {"detail": "Project deleted successfully"}


# Custom Domain Management Endpoints

@router.post("/projects/{project_id}/custom-domain")
def add_custom_domain(
    project_id: str,
    domain_data: CustomDomainIn,
    request: Request,
) -> DomainVerificationOut:
    """Add a custom domain to a project"""
    # Get project from request state or lookup by ID
    project = get_project_from_request(request)

    if not project:
        # Fallback to lookup by project_id if not in request state
        project = Project.find_one({"_id": ODMObjectId(project_id)})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    elif str(project.id) != project_id:
        # Ensure the project_id matches the project from request state
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project ID mismatch"
        )

    # Set the custom domain
    updated_project = set_custom_domain(project, domain_data.custom_domain)

    # Return verification instructions
    verification_record_name = get_verification_record_name(domain_data.custom_domain)
    verification_token = updated_project.domain_verification_token

    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate verification token"
        )

    return DomainVerificationOut(
        verification_token=verification_token,
        verification_record_name=verification_record_name,
        verification_record_value=verification_token,
        instructions=f"Add a TXT record to your DNS:\nName: {verification_record_name}\nValue: {verification_token}"
    )


@router.post("/projects/{project_id}/verify-domain")
def verify_domain(
    project_id: str,
    request: Request,
) -> dict[str, Any]:
    """Verify the custom domain for a project"""
    # Get project from request state or lookup by ID
    project = get_project_from_request(request)

    if not project:
        # Fallback to lookup by project_id if not in request state
        project = Project.find_one({"_id": ODMObjectId(project_id)})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    elif str(project.id) != project_id:
        # Ensure the project_id matches the project from request state
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project ID mismatch"
        )

    # Verify the domain
    is_verified = verify_custom_domain(project)

    if is_verified:
        return {
            "verified": True,
            "message": f"Domain {project.custom_domain} has been successfully verified!",
            "domain": project.custom_domain
        }
    else:
        custom_domain = project.custom_domain
        verification_token = project.domain_verification_token

        if not custom_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No custom domain found for this project"
            )

        return {
            "verified": False,
            "message": f"Domain {custom_domain} verification failed. Please check your DNS records.",
            "domain": custom_domain,
            "verification_token": verification_token,
            "record_name": get_verification_record_name(custom_domain)
        }


@router.delete("/projects/{project_id}/custom-domain")
def remove_domain(
    project_id: str,
    request: Request,
) -> dict[str, str]:
    """Remove custom domain from a project"""
    # Get project from request state or lookup by ID
    project = get_project_from_request(request)

    if not project:
        # Fallback to lookup by project_id if not in request state
        project = Project.find_one({"_id": ODMObjectId(project_id)})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    elif str(project.id) != project_id:
        # Ensure the project_id matches the project from request state
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project ID mismatch"
        )

    if not project.custom_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain associated with this project"
        )

    domain = project.custom_domain
    remove_custom_domain(project)

    return {"detail": f"Custom domain {domain} has been removed successfully"}


@router.get("/projects/{project_id}/custom-domain/instructions")
def get_domain_instructions(
    project_id: str,
    request: Request,
) -> dict[str, Any]:
    """Get detailed instructions for domain verification"""
    # Get project from request state or lookup by ID
    project = get_project_from_request(request)
    
    if not project:
        # Fallback to lookup by project_id if not in request state
        project = Project.find_one({"_id": ODMObjectId(project_id)})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    elif str(project.id) != project_id:
        # Ensure the project_id matches the project from request state
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project ID mismatch"
        )
    
    if not project.custom_domain or not project.domain_verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain or verification token found for this project"
        )
    
    # Get detailed instructions
    instructions = get_domain_verification_instructions(
        project.custom_domain, 
        project.domain_verification_token
    )
    
    return {
        "project_id": project_id,
        "project_title": project.title,
        "verification_status": "verified" if project.is_verified else "pending",
        **instructions
    }


@router.get("/domain-info")
def get_domain_info(request: Request) -> dict[str, Any]:
    """Get information about the current domain/subdomain"""
    domain_type = getattr(request.state, 'domain_type', 'unknown')
    host = getattr(request.state, 'host', 'unknown')
    subdomain = getattr(request.state, 'subdomain', None)
    project = get_project_from_request(request)
    
    return {
        "host": host,
        "domain_type": domain_type,
        "subdomain": subdomain,
        "project_id": str(project.id) if project else None,
        "project_title": project.title if project else None,
        "custom_domain": project.custom_domain if project else None,
        "is_verified": project.is_verified if project else None,
    }
