import os

from app.core.config import settings


def get_absolute_filepath(relative_path: str) -> str:
    """Convert a /static/... relative URL to an absolute filesystem path."""
    if os.environ.get("RUNNING_TESTS") == "1":
        static_dir = settings.TEST_STATIC_DIR
    else:
        static_dir = settings.STATIC_DIR
    return relative_path.replace("/static/", f"{static_dir}/", 1)
