import contextvars
import json
import logging
from datetime import datetime, timezone


request_id_var = contextvars.ContextVar("request_id", default="-")


class JsonLogFormatter(logging.Formatter):
    """Emit small structured records without request bodies or exception text."""

    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
