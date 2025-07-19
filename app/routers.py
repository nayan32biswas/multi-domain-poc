import logging
from typing import Any

from fastapi import APIRouter, Request

from app.models import Project
from app.schemas import ProjectIn, ProjectOut
from app.services import get_project_or_404
from app.utils import update_partially

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check() -> Any:
    return {"status": "ok"}


@router.get("/projects")
def get_projects(
    request: Request,
    subdomain: None | str = None,
    custom_domain: None | str = None,
) -> Any:
    print(f"project: {request.state.project}")
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


@router.put("/projects/{project_id}")
def update_project(project_data: ProjectIn, project_id: str):
    existing_project = get_project_or_404(project_id)

    existing_project = update_partially(existing_project, project_data)
    existing_project.update()

    return ProjectOut(**existing_project.model_dump())


@router.delete("/projects/{project_id}")
def delete_project(project_id: str):
    existing_project = get_project_or_404(project_id)

    existing_project.delete()

    return {"message": "Project deleted successfully"}
