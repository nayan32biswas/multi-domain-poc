from fastapi import HTTPException, status
from mongodb_odm import ODMObjectId

from app.models import Project


def get_project_or_404(subdomain: str, project_id: str) -> Project:
    existing_project = Project.find_one(
        {"_id": ODMObjectId(project_id), "subdomain": subdomain}
    )
    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return existing_project


def is_valid_subdomain(subdomain: str | None) -> bool:
    return Project.exists({"subdomain": subdomain})
