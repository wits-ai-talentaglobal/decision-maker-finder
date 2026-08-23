import logging
import sys

_FORMAT = "%(asctime)s %(levelname)s %(name)s job=%(job_id)s stage=%(stage)s %(message)s"


class _DefaultContextFilter(logging.Filter):
    """Ensures job_id/stage are always present so the format string never KeyErrors."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "job_id"):
            record.job_id = "-"
        if not hasattr(record, "stage"):
            record.stage = "-"
        return True


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))
    handler.addFilter(_DefaultContextFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    # httpx logs the full request URL at INFO, including any query-string API key
    # (e.g. Hunter.io's ?api_key=...) — raise its level so secrets never hit logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_stage_logger(name: str, job_id: int, stage: str) -> logging.LoggerAdapter:
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, {"job_id": job_id, "stage": stage})
