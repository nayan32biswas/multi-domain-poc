import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()


TIMEOUT_SEC = 60 * 3
BASE_DIR = Path(__file__).resolve().parent
sudo_path = shutil.which("sudo") or "/usr/bin/sudo"

DEBUG = os.environ.get("DEBUG", "True").strip().lower() == "true"

custom_domain_script_file = os.path.join(BASE_DIR, "configure-custom-domain.sh")
remove_custom_domain_script_file = os.path.join(BASE_DIR, "remove-custom-domain-config.sh")


class CustomDomain(BaseModel):
    custom_domain: str
    email: str


def get_custom_domain_config_args(data: CustomDomain) -> list[str]:
    custom_domain = data.custom_domain
    email = data.email

    command_args: Any = [sudo_path, custom_domain_script_file, custom_domain, email]
    if DEBUG:
        command_args += ["true"]

    return command_args


class RemoveCustomDomain(BaseModel):
    custom_domain: str


def get_remove_custom_domain_config_args(data: RemoveCustomDomain) -> list[str]:
    custom_domain = data.custom_domain

    command_args: Any = [sudo_path, remove_custom_domain_script_file, custom_domain]
    if DEBUG:
        command_args += ["true"]

    return command_args


def _script_executor(func: Any, data: Any) -> Any:
    try:
        command_args = func(data)

        print(f'Executing command: "{" ".join(command_args)}"')

        result = subprocess.run(
            command_args,
            text=True,
            capture_output=True,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.CalledProcessError as ex:
        print(f"Error executing script: {ex.output.decode()}")
        return HTTPException(
            detail={"error": ex.output.decode(), "code": ex.returncode},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as ex:
        print(f"Unexpected error: {str(ex)}")
        return HTTPException(
            detail={"error": str(ex), "code": 500},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.post("/configure-custom-domain")
async def configure_custom_domain(payload: CustomDomain) -> Any:
    return _script_executor(get_custom_domain_config_args, payload)


@app.post("/remove-custom-domain")
async def remove_custom_domain(payload: RemoveCustomDomain) -> Any:
    return _script_executor(get_remove_custom_domain_config_args, payload)
