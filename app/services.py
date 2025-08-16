import re
import secrets
import string
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from mongodb_odm import ODMObjectId

from app.config import SITE_DOMAIN
from app.models import Project

MAX_CONFIGURE_RETRY = 5
SUBDOMAIN_CHARS = string.ascii_lowercase + string.digits

instruction_template = """
To verify ownership of {domain}, please add the following DNS record:
Record Type: TXT
Name: {verification_record_name}
Value: {token}

After adding the TXT record, you also need to point your domain to our servers:

RECOMMENDED: Use CNAME (easier to manage)
Record Type: CNAME
Name: @ (or leave blank for root domain)
Value: {subdomain_host}

Record Type: CNAME
Name: www
Value: {subdomain_host}

After adding the record, it may take a few minutes to propagate. \
    Then use the verification endpoint to complete the process.

Example DNS configuration:
- If using cPanel: Go to Zone Editor, add TXT and CNAME records
- If using Cloudflare: Go to DNS settings, add TXT and CNAME records
- If using AWS Route53: Add TXT and CNAME records in hosted zone
- If using Namecheap: Go to Advanced DNS, add TXT and CNAME records

The records should look like:
{verification_record_name}    IN    TXT    "{token}"
{domain}    IN    CNAME    {subdomain_host}
www.{domain}    IN    CNAME    {subdomain_host}
"""

troubleshooting_template = """
If verification fails:
1. Check that the TXT record was added correctly
2. Wait 5-10 minutes for DNS propagation
3. Use online DNS lookup tools to verify the record exists
4. Ensure there are no typos in the record name or value
5. Some DNS providers require the full domain name including trailing dot
6. Make sure both TXT (for verification) and CNAME (for routing) records are added
7. Test domain accessibility: ping {domain}

If the custom domain configuration failed use "/api/projects/{project_id}/re-configure" API to retry the configuration.
"""

# Subdomain should not start or end with a hyphen, and must be 3-63 characters long
subdomain_regex = re.compile(r"^(?!-)[a-zA-Z0-9-]{3,63}(?<!-)$")
reserved_subdomains = {
    "www",
    "api",
    "admin",
    "static",
    "assets",
    "cdn",
    "blog",
    "docs",
    "support",
    "localhost",
    "dev",
    "staging",
    "test",
    "demo",
    "local",
    "app",
    "dashboard",
    "portal",
    "web",
    "mail",
    "shop",
    "store",
}


def get_sanitized_subdomain(subdomain: str) -> str | None:
    subdomain = subdomain.strip()

    if not subdomain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain cannot be empty",
        )

    if subdomain in reserved_subdomains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subdomain '{subdomain}' is reserved and cannot be used.",
        )

    if not subdomain_regex.match(subdomain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain can only contain alphanumeric characters, hyphens, and underscores.",
        )

    return subdomain


def generate_subdomain() -> str:
    """Generate a random subdomain"""

    def get_random_subdomain_str() -> str:
        # Generate a random string with only lowercase letters and numbers
        return "".join(secrets.choice(SUBDOMAIN_CHARS) for _ in range(8))

    for _ in range(10):  # Try up to 10 times to find a valid subdomain
        subdomain = get_random_subdomain_str()

        if subdomain in reserved_subdomains:
            continue

        if is_subdomain_available(subdomain):
            return subdomain

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to generate a unique subdomain after multiple attempts.",
    )


def get_sanitized_custom_domain(custom_domain: str | None) -> str | None:
    if not custom_domain:
        return None

    custom_domain = custom_domain.strip().lower()

    if not validate_domain_format(custom_domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid custom domain format. Please provide a valid domain.",
        )

    return custom_domain


def get_project_or_404(project_id: str, subdomain: str | None = None, custom_domain: str | None = None) -> Project:
    filter: dict[str, Any] = {"_id": ODMObjectId(project_id)}

    if subdomain:
        filter["subdomain"] = subdomain
    elif custom_domain:
        filter["custom_domain"] = custom_domain

    existing_project = Project.find_one(filter)
    if not existing_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return existing_project


def is_subdomain_available(subdomain: str) -> bool:
    existing_project = Project.find_one({"subdomain": subdomain})

    return existing_project is None


def is_customdomain_available(custom_domain: str) -> bool:
    existing_project = Project.find_one({"custom_domain": custom_domain})

    return existing_project is None


def get_project_by_custom_domain(domain: str) -> Project | None:
    """Get project by custom domain"""
    return Project.find_one({"custom_domain": domain, "is_active": True})


def generate_verification_token() -> str:
    """Generate a unique verification token"""
    return secrets.token_urlsafe(32)


def get_verification_record_name(domain: str) -> str:
    """Get the DNS record name for verification"""
    return f"_domain-verification.{domain}"


def validate_domain_format(domain: str) -> bool:
    """Validate domain format"""
    try:
        # Basic format validation
        if not domain or "." not in domain:
            return False

        parts = domain.split(".")
        if len(parts) < 2:
            return False

        # Check each part
        for part in parts:
            if not part or part.startswith("-") or part.endswith("-"):
                return False

            # Check if all characters are valid
            if not all(c.isalnum() or c == "-" for c in part):
                return False

        return True
    except Exception:
        return False


def check_domain_verification(domain: str, token: str) -> bool:
    """Check if domain is verified by looking up TXT record"""
    try:
        import dns.exception
        import dns.resolver
    except ImportError:
        print("❌ dnspython not installed. Install with: pip install dnspython")
        return False

    verification_record_name = get_verification_record_name(domain)

    print(f"Verifying domain {domain} with token {token}")
    print(f"Looking for TXT record: {verification_record_name} = {token}")

    try:
        # Configure resolver with timeout
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10  # 10 second timeout
        resolver.lifetime = 15  # 15 second total lifetime

        # Query TXT records for the verification record
        try:
            answers: Any = resolver.resolve(verification_record_name, "TXT")

            # Check if we have any records
            if not answers.rrset:
                print(f"❌ No TXT records found for {verification_record_name}")
                return False

            # Iterate through the TXT records in the rrset
            for txt_record in answers.rrset:
                # Convert the TXT record to string and clean it
                txt_content = str(txt_record).strip()

                # Remove surrounding quotes if present
                if txt_content.startswith('"') and txt_content.endswith('"'):
                    txt_value = txt_content[1:-1]
                elif txt_content.startswith("'") and txt_content.endswith("'"):
                    txt_value = txt_content[1:-1]
                else:
                    txt_value = txt_content

                print(f"Found TXT record: '{txt_value}'")

                # Check if this record matches our verification token
                if txt_value == token:
                    print(f"✅ Domain verification successful for {domain}")
                    return True

            print(f"❌ Verification token not found in TXT records for {verification_record_name}")
            print(f"Expected: '{token}'")
            return False

        except dns.resolver.NXDOMAIN:
            print(f"❌ DNS record {verification_record_name} does not exist")
            print("Please add the following TXT record to your DNS:")
            print(f"Name: {verification_record_name}")
            print(f"Value: {token}")
            return False

        except dns.resolver.NoAnswer:
            print(f"❌ No TXT records found for {verification_record_name}")
            return False

        except dns.resolver.Timeout:
            print(f"❌ DNS query timeout for {verification_record_name}")
            return False

    except dns.exception.DNSException as e:
        print(f"❌ DNS query failed for {verification_record_name}: {str(e)}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error during DNS verification: {str(e)}")
        return False


def get_domain_verification_instructions(token: str, domain: str, subdomain: str) -> dict[str, str]:
    """Get detailed instructions for domain verification"""
    verification_record_name = get_verification_record_name(domain)

    subdomain_host = f"{subdomain}.{SITE_DOMAIN}"

    instruction_data = instruction_template.format(
        domain=domain,
        subdomain_host=subdomain_host,
        token=token,
        verification_record_name=verification_record_name,
    )
    troubleshooting_data = troubleshooting_template.format(domain=domain)

    return {
        "domain": domain,
        "verification_token": token,
        "record_name": verification_record_name,
        "record_type": "TXT",
        "record_value": token,
        "instructions": instruction_data,
        "troubleshooting": troubleshooting_data,
    }


def set_custom_domain(project: Project, domain: str) -> Project:
    """Set custom domain for a project with verification token"""
    if not validate_domain_format(domain):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid domain format")

    # Check if domain is already taken
    existing_project = get_project_by_custom_domain(domain)
    if existing_project and existing_project.id != project.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain is already taken by another project",
        )

    # Generate verification token
    verification_token = generate_verification_token()

    # Update project
    project.custom_domain = domain
    project.domain_verification_token = verification_token
    project.is_verified = False
    project.domain_verified_at = None
    project.updated_at = datetime.now()

    project.update()
    return project


def verify_custom_domain(project: Project) -> bool:
    """Verify custom domain by checking DNS TXT record"""
    if not project.custom_domain or not project.domain_verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain or verification token found",
        )

    is_verified = check_domain_verification(project.custom_domain, project.domain_verification_token)

    if is_verified:
        project.is_verified = True
        project.domain_verified_at = datetime.now()
        project.updated_at = datetime.now()
        project.update()

    return is_verified


def remove_custom_domain(project: Project) -> Project:
    """Remove custom domain from a project"""
    project.custom_domain = None
    project.domain_verification_token = None
    project.is_verified = False
    project.domain_verified_at = None
    project.updated_at = datetime.now()

    project.update()

    return project
