"""Sentry tasks."""

import logging
import os

from invoke import Context, UnexpectedExit, task

from .utils import current_workspace

logger = logging.getLogger(__name__)
sentry_org = "radix-ai"
sentry_project = "sentiment-flanders"
sentry_release = "sentiment_flanders@0.0.0"


def release_exists(c: Context) -> bool:
    """Check if the current Sentry release exists."""
    try:
        c.run(f"sentry-cli releases --org {sentry_org} info {sentry_release}", hide="both")
    except UnexpectedExit:
        exists = False
    else:
        exists = True
    return exists


@task
def create_release(c):
    """Create and finalize a new Sentry release from the current version."""
    if "SENTRY_AUTH_TOKEN" not in os.environ:
        logger.warning("Please set SENTRY_AUTH_TOKEN to enable Sentry releases")
        return
    if release_exists(c):
        logger.info(f"Sentry release {sentry_release} already created")
    else:
        logger.info(f"Creating new Sentry release {sentry_org}/{sentry_release}...")
        c.run(f"sentry-cli releases --org {sentry_org} new -p {sentry_project} {sentry_release}")
        c.run(f"sentry-cli releases --org {sentry_org} set-commits --auto {sentry_release}")
        c.run(f"sentry-cli releases --org {sentry_org} finalize {sentry_release}")


@task
def create_deployment(c):
    """Create a Sentry release deployment from the current release."""
    if "SENTRY_AUTH_TOKEN" not in os.environ:
        logger.warning("Please set SENTRY_AUTH_TOKEN to enable Sentry releases")
        return
    sentry_env = current_workspace(c)
    logger.info(
        f"Creating a Sentry release deployment of {sentry_org}/{sentry_release} to {sentry_env}..."
    )
    c.run(f"sentry-cli releases --org {sentry_org} deploys {sentry_release} new --env {sentry_env}")
