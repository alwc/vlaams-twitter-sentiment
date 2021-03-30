"""Terraform tasks."""

import logging
import os

from invoke import task

logger = logging.getLogger(__name__)
REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@task
def create(c):
    """Recreate the conda environment."""
    logger.info("Recreating conda environment sentiment-flanders-env...")
    conda_env_path = os.path.join(REPO_PATH, "./.envs", "sentiment-flanders-env")
    c.run("conda-merge environment.run.yml environment.dev.yml > environment.yml")
    c.run(f"conda env create --prefix {conda_env_path} --file environment.yml --force")
    c.run("conda config --append envs_dirs .envs 2> /dev/null")
    c.run("rm environment.yml")


@task
def update(c):
    """Update the conda environment."""
    logger.info("Updating conda environment sentiment-flanders-env...")
    conda_env_path = os.path.join(REPO_PATH, "./.envs", "sentiment-flanders-env")
    c.run("conda-merge environment.run.yml environment.dev.yml > environment.yml")
    c.run(f"conda env update --prefix {conda_env_path} --file environment.yml --prune")
    c.run("rm environment.yml")
