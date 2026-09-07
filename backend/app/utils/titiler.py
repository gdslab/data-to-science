import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# D2S requests tiles with the "tilesize" query parameter introduced in TiTiler
# 2.0. Earlier releases only accept the removed "@{scale}x" path suffix.
TITILER_MIN_MAJOR_VERSION = 2


@dataclass
class TitilerStatus:
    """Result of the most recent TiTiler version probe."""

    version: Optional[str] = None
    compatible: Optional[bool] = None


titiler_status = TitilerStatus()


def parse_titiler_version(payload: Any) -> Optional[str]:
    """Return the TiTiler version reported by a /healthz payload.

    Args:
        payload (Any): Deserialized /healthz response body.

    Returns:
        Optional[str]: Version string, or None if the payload cannot be read.
    """
    if not isinstance(payload, dict):
        return None

    versions = payload.get("versions")
    if not isinstance(versions, dict):
        return None

    version = versions.get("titiler")

    return version if isinstance(version, str) else None


def parse_titiler_major_version(payload: Any) -> Optional[int]:
    """Return the TiTiler major version reported by a /healthz payload.

    Args:
        payload (Any): Deserialized /healthz response body.

    Returns:
        Optional[int]: Major version, or None if the payload cannot be read.
    """
    version = parse_titiler_version(payload)
    if version is None:
        return None

    try:
        return int(version.split(".")[0])
    except ValueError:
        return None


async def _fetch_healthz(url: str) -> Optional[Any]:
    """Return the body of a TiTiler /healthz response, or None if it failed.

    Args:
        url (str): Full URL for the /healthz endpoint.

    Returns:
        Optional[Any]: Deserialized response body, or None if unavailable.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None


def _record_titiler_version(payload: Any) -> TitilerStatus:
    """Log and cache the TiTiler version reported by a /healthz payload.

    Args:
        payload (Any): Deserialized /healthz response body.

    Returns:
        TitilerStatus: Updated status cache.
    """
    version = parse_titiler_version(payload)
    major_version = parse_titiler_major_version(payload)

    if major_version is None:
        logger.warning("Could not read TiTiler version from /healthz response")
        titiler_status.compatible = None
    elif major_version >= TITILER_MIN_MAJOR_VERSION:
        logger.info(f"TiTiler {version} detected")
        titiler_status.compatible = True
    else:
        logger.error(
            f"TiTiler {version} detected. D2S requires TiTiler "
            f"{TITILER_MIN_MAJOR_VERSION}.0 or later and raster tiles will fail "
            "until the titiler image is upgraded."
        )
        titiler_status.compatible = False

    titiler_status.version = version

    return titiler_status


async def verify_titiler_version(
    base_url: str, attempts: int = 6, delay: float = 10.0
) -> TitilerStatus:
    """Probe TiTiler and log whether the running version is supported.

    Retries while TiTiler is still starting up. Never raises, so an unreachable
    or unsupported tile server degrades raster tiles without stopping the API.

    Args:
        base_url (str): Base URL for the TiTiler service.
        attempts (int): Number of probes before giving up.
        delay (float): Seconds to wait between probes.

    Returns:
        TitilerStatus: Version reported by TiTiler and whether it is supported.
    """
    healthz_url = f"{base_url.rstrip('/')}/healthz"

    for attempt in range(1, attempts + 1):
        payload = await _fetch_healthz(healthz_url)
        if payload is not None:
            return _record_titiler_version(payload)
        if attempt < attempts:
            await asyncio.sleep(delay)

    logger.warning(f"Could not verify TiTiler version at {healthz_url}")
    titiler_status.version = None
    titiler_status.compatible = None

    return titiler_status
