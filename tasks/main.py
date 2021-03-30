"""Main tasks."""

import json
import logging
import os

from invoke import call, task

from . import aws, terraform

logger = logging.getLogger(__name__)
REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TFVARS_FILEPATH = os.path.join(
    REPO_PATH, "src", "sentiment_flanders", "config", "terraform.tfvars.json"
)


@task
def lint(c):
    """Lint this package."""
    logger.info("Running pre-commit checks...")
    c.run("pre-commit run --all-files --color always")


@task(
    pre=[
        call(terraform.deploy),
        call(aws.role, session_name="test-session", duration=3600, write_dotenv=False),
    ]
)
def test(c, pytest=True, behave=True):
    """Test this package."""
    if pytest:
        logger.info("Running Pytest...")
        c.run("env PYTHONPATH=src:$PYTHONPATH APP_DEBUG=1 pytest --cov=src tests/pytest", env=aws.ENV)
    if behave and os.path.exists(os.path.join(REPO_PATH, "tests", "behave")):
        logger.info("Running Behave...")
        c.run("env PYTHONPATH=src:$PYTHONPATH APP_DEBUG=1 behave tests/behave", env=aws.ENV)


@task(
    pre=[
        call(aws.role, session_name="lab-session", duration=36000, write_dotenv=False)
    ]
)
def lab(c, pytest=True, behave=True):
    """Run Jupyter Lab after assuming a role."""
    notebooks_path = os.path.join(REPO_PATH, "notebooks")
    os.makedirs(notebooks_path, exist_ok=True)
    with c.cd(notebooks_path):
        c.run("env PYTHONPATH=src:$PYTHONPATH jupyter lab", env=aws.ENV)


@task
def docs(c, browser=False, output_dir="site"):
    """Generate this package's docs."""
    if browser:
        c.run("env PYTHONPATH=src portray in_browser")
    else:
        c.run(f"env PYTHONPATH=src portray as_html --output_dir {output_dir} --overwrite")
        logger.info("Package documentation available at ./site/index.html")


@task
def bump(c, part, dry_run=False):
    """Bump the major, minor, patch, or post-release part of this package's version."""
    # Stage terraform.tfvars.json with the current git branch name.
    with open(TFVARS_FILEPATH) as f:
        tfvars = json.load(f)
    git_branch = c.run("git symbolic-ref --short HEAD", hide="out").stdout.strip()
    if tfvars["git_branch"] != git_branch:
        if dry_run:
            logger.info(f'terraform.tfvars.json would be updated with "git_branch": "{git_branch}"')
        else:
            tfvars["git_branch"] = git_branch
            with open(TFVARS_FILEPATH, "w") as f:
                json.dump(tfvars, f, indent=2)
            c.run(f"git add --update {TFVARS_FILEPATH}")
            c.run(f'git commit -m "Set git_branch to {git_branch} in terraform.tfvars.json"')
    # Bump the version with bump2version.
    c.run(f"bump2version {'--dry-run --verbose ' + part if dry_run else part}")


@task
def serve(c, browser=False, output_dir="site"):
    """Serve this package's REST API locally with uvicorn."""
    logger.info("Serving REST API locally with uvicorn...")
    c.run("env PYTHONPATH=src:$PYTHONPATH APP_DEBUG=1 uvicorn sentiment_flanders.api:app")
