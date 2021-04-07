"""Serverless tasks."""

import logging
import os
import re

from invoke import Context, call, task

from . import aws, terraform

logger = logging.getLogger(__name__)
REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACKAGE_PATH = os.path.join(REPO_PATH, "src")
print (PACKAGE_PATH)

@task(pre=[call(terraform.deploy, force=True)])
def install_plugins(c):
    """Install the Serverless plugins listed in serverless.yml."""
    logger.info("Installing Serverless plugins...")
    with open(os.path.join(PACKAGE_PATH, "serverless.yml")) as sls:
        for line in sls:
            match = re.search(r"^\s+-\s+(?P<plugin>serverless-[^\s\n\r]+)", line)
            if match:
                with c.cd(PACKAGE_PATH):
                    c.run(f"serverless plugin install -n {match.group('plugin')}")


@task(
    pre=[
        call(install_plugins),
        call(aws.role, session_name="serverless-deploy-session", duration=900, write_dotenv=False),
    ]
)
def deploy(c):
    """Deploy the package with Serverless to the active workspace account."""
    with c.cd(PACKAGE_PATH):
        logger.info("Updating Serverless deployment...")
        c.run("touch requirements.txt")
        c.run("serverless create_domain", env=aws.ENV)
        c.run("serverless deploy", env=aws.ENV)
        c.run("rm requirements.txt")


@task(
    pre=[
        call(install_plugins),
        call(aws.role, session_name="serverless-destroy-session", duration=900, write_dotenv=False),
    ]
)
def destroy(c, dry_run=True):
    """Destroy the Serverless deployment on the active workspace account."""
    with c.cd(PACKAGE_PATH):
        if dry_run:
            logger.info(f"Serverless remove dry-run for {aws.ENV['WORKSPACE']}")
        else:
            logger.warning("Destroying Serverless deployment...")
            c.run("serverless delete_domain", env=aws.ENV)
            c.run("serverless remove", env=aws.ENV)
