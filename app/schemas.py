from datetime import datetime

from mongodb_odm import ObjectIdStr
from pydantic import BaseModel, Field


class ProjectOut(BaseModel):
    id: ObjectIdStr
    title: str
    description: str | None = None
    subdomain: str
    custom_domain: str | None = None
    domain_verification_token: str | None = None
    domain_verified_at: datetime | None = None
    is_verified: bool = False
    is_active: bool = True
    is_configured: bool = False
    configure_retry_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectIn(BaseModel):
    title: str
    description: str | None = None


class CustomDomainIn(BaseModel):
    custom_domain: str = Field(..., description="The custom domain to add")


class DomainVerificationOut(BaseModel):
    verification_token: str
    verification_record_name: str
    verification_record_value: str
    instructions: str
