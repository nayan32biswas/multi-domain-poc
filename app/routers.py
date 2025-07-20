import logging
from typing import Any

from fastapi import APIRouter, Depends, Request

from app.config import DEBUG, LOCAL_SUBDOMAIN
from app.models import Project
from app.schemas import ProjectIn, ProjectOut
from app.services import get_project_or_404
from app.utils import update_partially

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


def get_subdomain_from_request(request: Request) -> str | None:
    subdomain = request.headers.get("X-Subdomain")
    if DEBUG is True and subdomain == LOCAL_SUBDOMAIN:
        return LOCAL_SUBDOMAIN
    if not subdomain:
        raise ValueError("Subdomain header is missing")

    return subdomain.lower()


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
