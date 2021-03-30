"""Package configuration."""

import logging
import os
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Optional

import dynaconf

__version__ = "0.0.0"
logger = logging.getLogger(__name__)


def get_workspace() -> Optional[str]:
    """Identify the current Terraform workspace name."""
    # Extract workspace from environment variables.
    workspace = os.environ.get("WORKSPACE") or os.environ.get("ENV_FOR_DYNACONF")
    if workspace:
        logger.info(f"Selected workspace {workspace} based on an environment variable")
        return workspace
    # Extract workspace from git branch name.
    try:
        git_branch = (
            os.environ.get("CI_COMMIT_REF_NAME")
            or check_output("git symbolic-ref --short HEAD".split())  # noqa: S603
            .decode("utf-8")
            .strip()
        )
    except CalledProcessError:
        logger.exception(f"Could not find a valid configuration to select the {workspace}")
        raise
    else:
        if git_branch in ("infrastructure", "feature", "development", "acceptance", "production"):
            workspace = git_branch
        elif git_branch == "master":
            workspace = "production"
        elif "infra" in git_branch:
            workspace = "infrastructure"
        else:
            workspace = "feature"
        logger.info(f"Selected workspace {workspace} based on the active git branch")
        return workspace


def load_config(workspace: Optional[str] = None) -> dynaconf.LazySettings:
    """Load package config for the selected workspace."""
    settings = dynaconf.LazySettings(
        ENV_FOR_DYNACONF=workspace or get_workspace(),
        ROOT_PATH_FOR_DYNACONF=os.path.dirname(__file__),
        LOADERS_FOR_DYNACONF=[
            "sentiment_flanders.config.terraform_loader",
            "dynaconf.loaders.env_loader",
        ],
    )
    return settings
