import logging
import json
import sys
from datetime import datetime, timezone


class MyLogger:
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)


    def _log(self, level, event, **kwargs):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "event": event,
            "data": kwargs
        }

        message = json.dumps(log_entry, ensure_ascii=False)
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
        sys.stderr.flush()

    def debug(self, event, **kwargs):
        self._log("DEBUG", event, **kwargs)

    def info(self, event, **kwargs):
        self._log("INFO", event, **kwargs)

    def warning(self, event, **kwargs):
        self._log("WARNING", event, **kwargs)

    def error(self, event, **kwargs):
        self._log("ERROR", event, **kwargs)

    def critical(self, event, **kwargs):
        self._log("CRITICAL", event, **kwargs)


log = MyLogger('Logger')
