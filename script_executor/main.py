import os
import subprocess
from enum import StrEnum
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


def to_bool(value: str) -> bool:
    return value.strip().lower() == "true"


DEBUG = to_bool(os.environ.get("DEBUG", "True"))
TIMEOUT_SEC = 60 * 3

custom_domain_script = "script_executor/configure-custom-domain.sh"


class ScriptType(StrEnum):
    CONFIGURE_CUSTOM_DOMAIN = "CONFIGURE_CUSTOM_DOMAIN"


class ScriptPayload(BaseModel):
    script_type: ScriptType
    data: dict[str, Any]


def configure_custom_domain(data: dict[str, Any]) -> str:
    custom_domain = data.get("custom_domain")
    email = data.get("email")

    if not custom_domain:
        raise ValueError("Custom domain is required")

    if not email:
        raise ValueError("Email is required")

    command_args: Any = ["sudo", "bash", custom_domain_script, custom_domain, email]
    if DEBUG:
        command_args.append("true")

    output = subprocess.check_output(
        command_args,
        stderr=subprocess.STDOUT,
        timeout=TIMEOUT_SEC,
    )

    return output.decode()


execution_map = {
    ScriptType.CONFIGURE_CUSTOM_DOMAIN: configure_custom_domain,
}


@app.post("/run-script")
async def run_script(payload: ScriptPayload) -> Any:
    script_type = payload.script_type
    execution_function = execution_map.get(script_type)

    if not execution_function:
        return {"error": f"Script type '{script_type}' not supported"}

    try:
        output = execution_function(payload.data)
        return {"output": output}
    except subprocess.CalledProcessError as e:
        return {"error": e.output.decode(), "code": e.returncode}
    except Exception as ex:
        return {"error": str(ex), "code": 500}
