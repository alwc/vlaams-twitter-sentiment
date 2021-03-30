"""AWS tasks."""

import json
import logging
import os
from typing import Any, Dict

from invoke import Context, UnexpectedExit, task

from .utils import current_workspace

logger = logging.getLogger(__name__)

ORIG_ENV = os.environ.copy()
ENV: Dict[str, str] = {}  # Save role credentials once a role is assumed.
REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def current_aws_account(c: Context) -> str:
    """Get AWS account corresponding to the active git branch."""
    aws_account = {'infrastructure': '962194010810', 'feature': '962194010810', 'development': '962194010810', 'acceptance': '962194010810', 'production': '962194010810'}.get(current_workspace(c), "feature")
    return aws_account


def role_credentials(
    c: Context,
    role: str = "OrganizationAccountAccessRole",
    session_name: str = "user-session",
    duration: int = 36000,
) -> Dict[str, Any]:
    """Get credentials for a role for the workspace corresponding to the active git branch."""
    workspace = current_workspace(c)
    aws_account = current_aws_account(c)
    if os.environ.get("AWS_SESSION_TOKEN"):
        os.environ.clear()
        os.environ.update(ORIG_ENV)
    try:
        role_creds: Dict[str, Any] = json.loads(
            c.run(
                f"aws sts assume-role "
                f"--role-arn arn:aws:iam::{aws_account}:role/{role} "
                f"--role-session-name {session_name} "
                f"--duration-seconds {duration}",
                hide="both",
            ).stdout
        )
    except UnexpectedExit:
        if duration > 3600:
            logger.warning(
                f"Could not assume {role} for {duration // 60} minutes, trying again with 60 minutes..."
            )
            duration = 3600
        elif duration < 900:
            logger.warning(
                f"Could not assume {role} for {duration // 60} minutes, trying again with 15 minutes..."
            )
            duration = 900
        else:
            logger.error(f"Could not assume {role} for {duration // 60} minutes")
            raise
        role_creds: Dict[str, Any] = json.loads(
            c.run(
                f"aws sts assume-role "
                f"--role-arn arn:aws:iam::{aws_account}:role/{role} "
                f"--role-session-name {session_name} "
                f"--duration-seconds {duration}",
                hide="out",
            ).stdout
        )
    role_creds["env"] = {
        "WORKSPACE": workspace,
        "AWS_ACCOUNT": aws_account,
        "AWS_DEFAULT_REGION": "eu-west-1",
        "AWS_SESSION_TOKEN": role_creds["Credentials"]["SessionToken"],
        "AWS_ACCESS_KEY_ID": role_creds["Credentials"]["AccessKeyId"],
        "AWS_SECRET_ACCESS_KEY": role_creds["Credentials"]["SecretAccessKey"],
    }
    logger.info(f"Assumed {role} for {session_name} valid for {duration // 60} minutes")
    return role_creds


@task
def role(
    c,
    role="OrganizationAccountAccessRole",
    session_name="user-session",
    duration=36000,
    write_dotenv=True,
):
    """Assume a role on AWS by writing a .env file."""
    role_creds = role_credentials(c, role, session_name, duration)
    os.environ.update(role_creds["env"])
    ENV.update(role_creds["env"])
    if write_dotenv:
        with open(".env", "w") as dotenv:
            dotenv.write(
                f"# workspace={role_creds['env']['WORKSPACE']} "
                f"role={role} "
                f"duration={duration} "
                f"session={session_name} "
                f"expires={role_creds['Credentials']['Expiration']}\n"
                f"AWS_SESSION_TOKEN={role_creds['env']['AWS_SESSION_TOKEN']}\n"
                f"AWS_ACCESS_KEY_ID={role_creds['env']['AWS_ACCESS_KEY_ID']}\n"
                f"AWS_SECRET_ACCESS_KEY={role_creds['env']['AWS_SECRET_ACCESS_KEY']}\n"
                f"PYTHONPATH=src:{os.environ.get('PYTHONPATH', '')}\n"
            )
