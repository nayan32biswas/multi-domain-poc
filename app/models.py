from datetime import datetime

from mongodb_odm import ASCENDING, Document, Field, IndexModel


class Project(Document):
    title: str = Field(required=True)
    description: str | None = Field(default=None)
    subdomain: str | None = Field(default=None)
    custom_domain: str | None = Field(default=None)
    domain_verification_token: str | None = Field(default=None)
    domain_verified_at: datetime | None = Field(default=None)
    is_verified: bool = Field(default=False)
    ssl_enabled: bool = Field(default=False)
    ssl_certificate_path: str | None = Field(default=None)
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class ODMConfig(Document.ODMConfig):
        collection_name = "project"
        indexes = [
            IndexModel([("title", ASCENDING)], unique=True),
            IndexModel([("subdomain", ASCENDING)]),
            IndexModel([("custom_domain", ASCENDING)]),
        ]
