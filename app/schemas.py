from datetime import datetime

from mongodb_odm import ObjectIdStr
from pydantic import BaseModel


class ProjectOut(BaseModel):
    id: ObjectIdStr
    title: str
    description: str | None = None
    subdomain: str | None = None
    custom_domain: str | None = None
    is_verified: bool = False
    ssl_enabled: bool = False
    is_active: bool = True
    created_at: datetime


class ProjectIn(BaseModel):
    title: str
    description: str | None = None
    subdomain: str | None = None
    custom_domain: str | None = None
