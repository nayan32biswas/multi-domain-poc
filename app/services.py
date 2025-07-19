from fastapi import HTTPException, status
from mongodb_odm import ODMObjectId

from app.models import Project


def get_project_or_404(project_id: str) -> Project:
    existing_project = Project.find_one({"_id": ODMObjectId(project_id)})
    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return existing_project


def get_project_by_subdomain(subdomain: str | None) -> Project | None:
    project = Project.find_one({"subdomain": subdomain})

    return project
