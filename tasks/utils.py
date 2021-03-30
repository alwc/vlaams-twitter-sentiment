"""Utility functions."""

import os

from invoke import Context


def current_git_branch(c: Context) -> str:
    """Get the active git branch name."""
    git_branch = (
        os.environ.get("CI_COMMIT_REF_NAME")
        or c.run("git symbolic-ref --short HEAD", hide="out").stdout.strip()
    )
    return git_branch


def current_workspace(c: Context) -> str:
    """Get the workspace corresponding to the active git branch."""
    git_branch = current_git_branch(c)
    if git_branch in ("infrastructure", "feature", "development", "acceptance", "production"):
        workspace = git_branch
    elif git_branch == "master":
        workspace = "production"
    elif "infra" in git_branch:
        workspace = "infrastructure"
    else:
        workspace = "feature"
    return workspace
