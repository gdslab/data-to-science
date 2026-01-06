import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from fastapi.encoders import jsonable_encoder
from pystac import Collection, Item
from pystac_client import Client
from pystac_client.exceptions import APIError

from app.core.config import settings
from app.schemas import STACReport, ItemStatus, STACError

logger = logging.getLogger(__name__)


# Custom Exceptions
class STACAPIError(Exception):
    """Base exception for STAC API errors."""

    pass


class STACConnectionError(STACAPIError):
    """Raised when unable to connect to STAC API."""

    pass


class STACPublishError(STACAPIError):
    """Raised when publishing to STAC catalog fails."""

    pass


class STACConfigurationError(STACAPIError):
    """Raised when STAC configuration is invalid or missing."""

    pass


class STACCollectionManager:
    """Manages STAC collections and items in a STAC API catalog.

    This class provides methods to publish, update, fetch, and remove
    STAC collections and items from a remote STAC API.
    """

    # API Configuration
    STAC_API_KEY_ENV = "STAC_API_KEY"
    STAC_API_KEY_HEADER = "D2S-STAC-API-Key"

    # HTTP
    CONTENT_TYPE_JSON = "application/json"
    HTTP_SUCCESS_CODES = (200, 201)
    HTTP_NOT_FOUND = 404
    API_TIMEOUT_SECONDS = 5

    # Error Codes
    ERROR_CODE_API_UNAVAILABLE = "API_UNAVAILABLE"
    ERROR_CODE_PUBLISH_FAILED = "PUBLISH_FAILED"

    def __init__(
        self,
        collection_id: str,
        collection: Optional[Collection] = None,
        items: Optional[List[Item]] = None,
    ) -> None:
        # Get and validate STAC API URL from settings
        self.api_url = self._get_stac_api_url()

        # Verify API is available
        if not self.__class__.is_stac_api_available():
            logger.error(f"STAC API at {self.api_url} is unavailable")
            raise STACConnectionError(f"STAC API at {self.api_url} is unavailable.")

        self.collection_id = collection_id
        self.collection = collection
        self.items = items or []

        logger.debug(
            f"Initialized STACCollectionManager for collection {collection_id}"
        )

    def _get_stac_api_url(self) -> str:
        """Get and validate STAC API URL from settings.

        Returns:
            STAC API URL as string

        Raises:
            STACConfigurationError: If STAC_API_URL is not configured in settings
        """
        if not settings.get_stac_api_url:
            logger.error("STAC_API_URL environment setting is not set")
            raise STACConfigurationError("STAC_API_URL environment setting is not set.")
        return str(settings.get_stac_api_url)

    def _get_client(self) -> Client:
        """Get connected STAC API client.

        Returns:
            Connected pystac_client.Client instance

        Raises:
            APIError: If unable to connect to STAC API
        """
        logger.info(f"Connecting to STAC API at {self.api_url}")
        return Client.open(self.api_url)

    def _get_api_key(self) -> str:
        """Get and validate STAC API key from environment.

        Returns:
            STAC API key string

        Raises:
            STACConfigurationError: If STAC_API_KEY environment variable is not set
        """
        api_key = os.getenv(self.STAC_API_KEY_ENV)
        if not api_key:
            logger.error(f"{self.STAC_API_KEY_ENV} environment variable is not set")
            raise STACConfigurationError(f"{self.STAC_API_KEY_ENV} environment variable is not set")
        return api_key

    def _build_headers(self, include_content_type: bool = False) -> dict:
        """Build request headers with API key.

        Args:
            include_content_type: Whether to include Content-Type header

        Returns:
            Dictionary of HTTP headers
        """
        headers = {self.STAC_API_KEY_HEADER: self._get_api_key()}
        if include_content_type:
            headers["Content-Type"] = self.CONTENT_TYPE_JSON
        return headers

    def fetch_public_collection(self) -> Optional[Dict]:
        """Get STAC Collection in public catalog.

        Raises:
            APIError: Raised if client fails to connect due to API being down.
            STACAPIError: Raised if collection cannot be transformed to dict.

        Returns:
            Optional[Dict]: Collection as dict, or None if collection not found.
        """
        try:
            # Connect to STAC API and retrieve collection
            client = self._get_client()
            logger.debug(f"Fetching collection {self.collection_id}")
            collection = client.get_collection(self.collection_id)
        except APIError as e:
            # Check if this is a 404 error (collection not found)
            if hasattr(e, "status_code") and e.status_code == self.HTTP_NOT_FOUND:
                logger.info(
                    f"Collection {self.collection_id} not found in STAC catalog"
                )
                return None
            else:
                # This is a different API error (like connection issue)
                logger.error(
                    f"Failed to connect to STAC API or fetch collection {self.collection_id}: {str(e)}"
                )
                raise

        if not collection:
            logger.info(f"Collection {self.collection_id} not found in STAC catalog")
            return None

        try:
            # Transform Collection to dict
            logger.debug(f"Transforming collection {self.collection_id} to dict")
            collection_d = collection.to_dict()
        except Exception as e:
            logger.error(
                f"Failed to transform collection {self.collection_id} to dict: {str(e)}"
            )
            raise STACAPIError(f"Failed to transform collection to dict: {str(e)}")

        logger.info(f"Successfully fetched collection {self.collection_id}")
        return collection_d

    def _fetch_items(self, as_dict: bool = False) -> List:
        """Internal method to fetch STAC items from public catalog.

        Args:
            as_dict: If True, return full item dictionaries. If False, return only IDs.

        Returns:
            List of item IDs (strings) or item dictionaries

        Raises:
            Exception: Any error during fetching (logged and returns empty list)
        """
        try:
            # Connect to STAC API and retrieve items
            client = self._get_client()
            logger.debug(f"Fetching items for collection {self.collection_id}")
            items = client.get_collection(self.collection_id).get_items()

            # Return full dicts or just IDs based on parameter
            if as_dict:
                return [item.to_dict() for item in items]
            else:
                return [item.id for item in items]

        except Exception as e:
            logger.error(
                f"Failed to fetch items for collection {self.collection_id}: {str(e)}"
            )
            # Return empty list instead of None to avoid errors downstream
            return []

    def fetch_public_items(self) -> List[str]:
        """Get STAC Item IDs in public catalog.

        Returns:
            List[str]: List of published item IDs associated with collection.
        """
        return self._fetch_items(as_dict=False)

    def fetch_public_items_full(self) -> List[Dict]:
        """Get full STAC Items in public catalog.

        Returns:
            List[Dict]: List of published items as dictionaries associated with collection.
        """
        return self._fetch_items(as_dict=True)

    def fetch_public_item(self, item_id: str) -> Optional[Dict]:
        """Get STAC Item in public catalog.

        Returns:
            Optional[Dict]: Item as dict, or None if item not found.
        """
        try:
            # Connect to STAC API and retrieve item
            client = self._get_client()
            logger.debug(f"Fetching item {item_id}")
            item = client.get_collection(self.collection_id).get_item(item_id)
        except APIError as e:
            # Check if this is a 404 error (item not found)
            if hasattr(e, "status_code") and e.status_code == self.HTTP_NOT_FOUND:
                logger.info(
                    f"Item {item_id} in collection {self.collection_id} not found in STAC catalog"
                )
                return None
            else:
                # This is a different API error (like connection issue)
                logger.error(
                    f"Failed to connect to STAC API or fetch item {item_id} in collection {self.collection_id}: {str(e)}"
                )
                raise

        if not item:
            logger.info(
                f"Item {item_id} in collection {self.collection_id} not found in STAC catalog"
            )
            return None

        try:
            # Transform Item to dict
            logger.debug(f"Transforming item {item_id} to dict")
            item_d = item.to_dict()
        except Exception as e:
            logger.error(f"Failed to transform item {item_id} to dict: {str(e)}")
            raise STACAPIError(f"Failed to transform item to dict: {str(e)}")

        logger.info(
            f"Successfully fetched item {item_id} in collection {self.collection_id}"
        )
        return item_d

    def compare_and_update(self) -> None:
        """Compare STAC Collection from public catalog with new STAC
        Collection. Update public catalog if there are changes.
        """
        try:
            logger.info(f"Comparing collection {self.collection_id} with local version")
            public_collection = self.fetch_public_collection()

            if not self.collection:
                logger.error("No local collection provided for comparison")
                raise STACConfigurationError("No local collection provided for comparison")

            local_collection_dict = self.collection.to_dict()

            # Update public collection with local_collection if different
            if local_collection_dict != public_collection:
                logger.info(
                    f"Collection {self.collection_id} has changes, publishing update"
                )
                self.publish_to_catalog()
            else:
                logger.info(f"Collection {self.collection_id} is up to date")
        except Exception as e:
            logger.error(f"Error during collection comparison: {str(e)}")
            raise

    def _validate_collection(self) -> None:
        """Validate that collection is set for publishing.

        Raises:
            STACConfigurationError: If no collection is set
        """
        if not self.collection:
            logger.error("No collection provided for publishing")
            raise STACConfigurationError("No collection provided for publishing")

    def _create_initial_report(self) -> STACReport:
        """Create initial STAC report with default values.

        Returns:
            STACReport with initial state
        """
        return STACReport(
            collection_id=self.collection_id,
            items=[],
            is_published=False,
            collection_url=f"{self.api_url}/collections/{self.collection_id}",
            error=None,
        )

    def _publish_collection(self, stac_report: STACReport) -> bool:
        """Publish or update the collection in the STAC catalog.

        Args:
            stac_report: Report to update if errors occur

        Returns:
            True if collection was published successfully, False otherwise
        """
        try:
            # Check if collection already exists
            existing_collection = self.fetch_public_collection()
        except APIError as e:
            # If we can't connect to the API, we can't publish
            logger.error(
                f"Cannot publish collection {self.collection_id}: API is unavailable"
            )
            stac_report.error = STACError(
                code=self.ERROR_CODE_API_UNAVAILABLE,
                message="STAC API is unavailable",
                timestamp=datetime.now(tz=timezone.utc),
                details={"error": str(e)},
            )
            return False

        # Build headers and prepare collection data
        headers = self._build_headers(include_content_type=True)
        collection_data = self.collection.to_dict()

        # Determine endpoint and method based on whether collection exists
        if existing_collection:
            logger.info(
                f"Collection {self.collection_id} exists, updating with PUT"
            )
            endpoint = f"{self.api_url}/collections/{self.collection_id}"
            response = requests.put(endpoint, headers=headers, json=collection_data)
        else:
            logger.info(
                f"Collection {self.collection_id} doesn't exist, creating with POST"
            )
            endpoint = f"{self.api_url}/collections"
            response = requests.post(endpoint, headers=headers, json=collection_data)

        # Check response
        if response.status_code not in self.HTTP_SUCCESS_CODES:
            logger.error(
                f"Failed to publish collection {self.collection_id}: {response.status_code} {response.text}"
            )
            stac_report.error = STACError(
                code=self.ERROR_CODE_PUBLISH_FAILED,
                message="Failed to publish collection",
                timestamp=datetime.now(tz=timezone.utc),
                details={"error": response.text},
            )
            return False

        # Update published status in report
        stac_report.is_published = True
        logger.info(f"Successfully published collection {self.collection_id}")
        return True

    def _publish_single_item(
        self,
        item: dict,
        public_item_ids: List[str],
        headers: dict,
    ) -> ItemStatus:
        """Publish or update a single STAC item.

        Args:
            item: Item dictionary to publish
            public_item_ids: List of currently published item IDs
            headers: HTTP headers for the request

        Returns:
            ItemStatus indicating success or failure
        """
        # Create item status
        item_status = ItemStatus(
            item_id=item["id"],
            is_published=False,
            item_url=f"{self.api_url}/collections/{self.collection_id}/items/{item['id']}",
            error=None,
        )

        # Use FastAPI's jsonable_encoder to handle datetime objects
        jsonable_item = jsonable_encoder(item)

        # Determine endpoint and method based on whether item exists
        if item["id"] not in public_item_ids:
            logger.info(f"Publishing item {item['id']} to catalog")
            endpoint = f"{self.api_url}/collections/{self.collection_id}/items"
            response = requests.post(endpoint, headers=headers, json=jsonable_item)
        else:
            logger.info(f"Updating item {item['id']} in catalog")
            endpoint = f"{self.api_url}/collections/{self.collection_id}/items/{item['id']}"
            response = requests.put(endpoint, headers=headers, json=jsonable_item)

        # Check response
        if response.status_code not in self.HTTP_SUCCESS_CODES:
            logger.error(
                f"Failed to publish item {item['id']}: {response.status_code} {response.text}"
            )
            item_status.error = STACError(
                code=self.ERROR_CODE_PUBLISH_FAILED,
                message="Failed to publish item",
                timestamp=datetime.now(tz=timezone.utc),
                details={"error": response.text},
            )
        else:
            # Update item status
            item_status.is_published = True
            logger.info(f"Successfully published item {item['id']}")

        return item_status

    def _publish_items(self, stac_report: STACReport) -> None:
        """Publish all items to the STAC catalog.

        Args:
            stac_report: Report to add item statuses to
        """
        # Get currently published item IDs
        public_item_ids = self.fetch_public_items()

        # Prepare items data
        items_data = [item.to_dict() for item in self.items]

        # Build headers
        headers = self._build_headers(include_content_type=True)

        # Publish each item
        for item in items_data:
            item_status = self._publish_single_item(item, public_item_ids, headers)
            stac_report.items.append(item_status)

    def publish_to_catalog(self) -> STACReport:
        """Publish STAC Collection and items to public catalog.

        This is the main orchestrator method that coordinates the publishing process:
        1. Validates collection is set
        2. Creates initial report
        3. Publishes/updates the collection
        4. Publishes/updates all items

        Returns:
            STACReport with publishing results

        Raises:
            STACConfigurationError: If collection is not set
            Exception: For other unexpected errors
        """
        try:
            logger.info(f"Publishing collection {self.collection_id} to catalog")

            # Validate and prepare
            self._validate_collection()
            stac_report = self._create_initial_report()

            # Publish collection
            collection_published = self._publish_collection(stac_report)
            if not collection_published:
                return stac_report

            # Publish items
            self._publish_items(stac_report)

            return stac_report

        except Exception as e:
            logger.error(f"Failed to publish collection {self.collection_id}: {str(e)}")
            raise

    def remove_from_catalog(self) -> None:
        """Remove STAC Collection from public catalog."""
        try:
            logger.info(f"Removing collection {self.collection_id} from catalog")

            # Build headers
            headers = self._build_headers()

            # Use DELETE method with the collection-specific endpoint
            endpoint = f"{self.api_url}/collections/{self.collection_id}"
            response = requests.delete(endpoint, headers=headers)

            if response.status_code != 200:
                if response.status_code == self.HTTP_NOT_FOUND:
                    logger.info(
                        f"Collection {self.collection_id} not found in STAC catalog"
                    )
                else:
                    logger.error(
                        f"Failed to remove collection {self.collection_id}: {response.status_code} {response.text}"
                    )
                    raise STACPublishError(
                        f"Failed to remove collection {self.collection_id}: {response.status_code} {response.text}"
                    )
            else:
                logger.info(f"Successfully removed collection {self.collection_id}")
        except Exception as e:
            logger.error(f"Failed to remove collection {self.collection_id}: {str(e)}")
            raise

    @classmethod
    def is_stac_api_available(cls) -> bool:
        """Check if public STAC API is accessible."""
        try:
            stac_url = settings.get_stac_api_url
            if not stac_url:
                logger.warning("STAC API URL is not configured")
                return False

            logger.debug(f"Checking if STAC API at {stac_url} is available")
            response = requests.get(str(stac_url), timeout=cls.API_TIMEOUT_SECONDS)
            is_available = response.status_code == 200
            if not is_available:
                logger.warning(
                    f"STAC API at {stac_url} returned status code {response.status_code}"
                )
            return is_available
        except requests.RequestException as e:
            logger.warning(f"STAC API at {stac_url} is unavailable: {str(e)}")
            return False
