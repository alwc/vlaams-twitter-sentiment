"""Terraform outputs loader."""

import functools
import json
import logging
import os
from typing import Any, Dict, Optional

import dynaconf

logger = logging.getLogger(__name__)
TFVARS_FILEPATH = os.path.join(os.path.dirname(__file__), "terraform.tfvars.json")
TFOUTS_FILEPATH = os.path.join(os.path.dirname(__file__), "terraform.outputs.json")


@functools.lru_cache(maxsize=8)
def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON object."""
    with open(filepath) as f:
        json_object: Dict[str, Any] = json.load(f)
    logger.info(f"Loaded {os.path.basename(filepath)}")
    return json_object


@functools.lru_cache(maxsize=8)
def load_tfouts(workspace: str) -> Dict[str, Any]:
    """Load the Terraform outputs for the selected workspace from the Parameter Store."""
    import boto3

    tfvars = load_json_file(TFVARS_FILEPATH)
    ssm = boto3.client("ssm", region_name=tfvars["region"])
    deploy_id = "latest"
    parameter = f"/{workspace}/sentiment-flanders/{deploy_id}"
    tfouts: Dict[str, Any] = json.loads(
        ssm.get_parameter(Name=parameter, WithDecryption=True)
        .get("Parameter", {})
        .get("Value", "{}")
    )
    logger.info(f"Loaded terraform outputs from the Parameter Store parameter {parameter}")
    return tfouts


def load(
    obj: dynaconf.base.Settings,
    env: Optional[str] = None,
    silent: bool = True,
    key: Optional[str] = None,
    filename: Optional[str] = None,
) -> None:
    """Load Terraform vars and outputs for the selected workspace."""
    workspace = (env or "").lower()
    # Load terraform.tfvars.json.
    try:
        tfvars = load_json_file(TFVARS_FILEPATH)
    except Exception:
        logger.exception(f"Could not load sentiment_flanders terraform.tfvars.json on {workspace}")
        raise
    obj.update(tfvars)
    # Load terraform.outputs.json locally or remotely.
    try:
        tfouts = load_json_file(TFOUTS_FILEPATH)
    except Exception:
        try:
            tfouts = load_tfouts(workspace=workspace)
        except Exception:
            logger.exception(f"Could not load sentiment_flanders terraform outputs on {workspace}")
            raise
    obj.update(tfouts)
