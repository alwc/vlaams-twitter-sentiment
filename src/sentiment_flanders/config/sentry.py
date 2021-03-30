"""Sentry.io configuration."""

import ast
import inspect
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional

import sentry_sdk
import wrapt
from sentry_sdk.integrations import aws_lambda

from . import config

# https://docs.sentry.io/error-reporting/configuration/?platform=python#common-options
sentry_client = sentry_sdk.Hub(
    sentry_sdk.Client(
        dsn="https://a82596eaa56c4ddeb8a4f89079a38730@o348638.ingest.sentry.io/5469393",
        release=f"sentiment_flanders@{config.__version__}",
        environment=config.get_workspace(),
        traces_sample_rate=1.0,
        # https://github.com/getsentry/sentry-python/issues/227
        integrations=[aws_lambda.AwsLambdaIntegration()],
    )
)


@wrapt.decorator
def log_function_with_sentry(
    wrapped: Callable[..., Any], instance: Any, args: List[Any], kwargs: Dict[str, Any]
) -> Any:
    """Attaches Sentry integrations to a function."""
    with sentry_client:
        try:
            return wrapped(*args, **kwargs)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise


@wrapt.decorator
async def log_function_with_sentry_async(
    wrapped: Callable[..., Any], instance: Any, args: List[Any], kwargs: Dict[str, Any]
) -> Any:
    """Attaches Sentry integrations to a function."""
    with sentry_client:
        try:
            return await wrapped(*args, **kwargs)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise


def log_module_with_sentry(module: Optional[ModuleType] = None) -> None:
    """Attaches Sentry integrations to a module."""
    module = module or inspect.getmodule(inspect.stack()[1][0])
    for node in ast.parse(inspect.getsource(module)).body:  # type: ignore
        if isinstance(node, ast.ClassDef):
            cls = getattr(module, node.name)
            for key, value in cls.__dict__.items():
                if callable(value) or isinstance(value, (classmethod, staticmethod)):
                    setattr(cls, key, log_function_with_sentry(value))
        elif isinstance(node, ast.FunctionDef):
            setattr(module, node.name, log_function_with_sentry(getattr(module, node.name)))
        elif isinstance(node, ast.AsyncFunctionDef):
            setattr(module, node.name, log_function_with_sentry_async(getattr(module, node.name)))
