"""Package tasks."""

from invoke import Collection

from . import aws, conda, sentry, serverless, terraform
from .logging import configure_root_logger
from .main import bump, docs, lab, lint, serve, test

configure_root_logger()

ns = Collection()
ns.add_task(bump)
ns.add_task(docs)
ns.add_task(lab)
ns.add_task(lint)
ns.add_task(serve)
ns.add_task(test)
ns.add_collection(aws)
ns.add_collection(conda)
ns.add_collection(sentry)
ns.add_collection(terraform)
ns.add_collection(serverless)
