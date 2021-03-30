"""Package cron handlers."""
from typing import Any, Dict

from sentiment_flanders.config import log_module_with_sentry


def cron_handler(event: Any, context: Any) -> Dict[str, Any]:
    """Scheduled function demo."""
    return {"invoked": context.function_name}


log_module_with_sentry()
