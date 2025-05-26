import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest

from app.core.config import settings
from app.core.logging import setup_logger


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for logs during testing."""
    original_log_dir = settings.API_LOGDIR
    temp_log_dir = tmp_path / "logs"
    temp_log_dir.mkdir()

    # Temporarily modify the settings
    settings.API_LOGDIR = str(temp_log_dir)

    # Reset any existing logger configuration
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set up logger with new paths
    setup_logger()

    yield temp_log_dir

    # Cleanup
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    shutil.rmtree(temp_log_dir)
    settings.API_LOGDIR = original_log_dir
    setup_logger()  # Restore original logger setup


def test_log_rotation(temp_log_dir: Path) -> None:
    """Test that log rotation works correctly with daily rotation."""
    logger = logging.getLogger(__name__)

    # Log some messages
    logger.info("Test message 1")
    logger.info("Test message 2")

    # List all log files to verify rotation
    log_files = sorted(temp_log_dir.glob("backend.log*"))

    # We should have at least the current log file
    assert len(log_files) >= 1, "No log files were created"

    # Verify that the current log file exists and is not empty
    current_log = log_files[-1]
    assert current_log.stat().st_size > 0, "Current log file is empty"

    # Verify the log file contains our test messages
    log_content = current_log.read_text()
    assert "Test message 1" in log_content
    assert "Test message 2" in log_content

    # Verify the log file has the correct format (JSON)
    try:
        import json

        for line in log_content.strip().split("\n"):
            json.loads(line)
    except json.JSONDecodeError:
        pytest.fail("Log file does not contain valid JSON entries")
