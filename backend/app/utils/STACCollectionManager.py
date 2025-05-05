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


class STACCollectionManager:
    STAC_API_URL = settings.STAC_API_URL

    def __init__(
        self,
        collection_id: str,
        collection: Optional[Collection] = None,
        items: Optional[List[Item]] = None,
    ) -> None:
        if not self.STAC_API_URL:
            logger.error("STAC_API_URL environment setting is not set")
            raise ValueError("STAC_API_URL environment setting is not set.")

        if not self.__class__.is_stac_api_available():
            logger.error(f"STAC API at {self.STAC_API_URL} is unavailable")
            raise ConnectionError(f"STAC API at {self.STAC_API_URL} is unavailable.")

        self.api_url = str(self.STAC_API_URL)
        self.collection_id = collection_id
        self.collection = collection
        self.items = items or []

        logger.debug(
            f"Initialized STACCollectionManager for collection {collection_id}"
        )

    def fetch_public_collection(self) -> Optional[Dict]:
        """Get STAC Collection in public catalog.

        Raises:
            APIError: Raised if client fails to connect due to API being down.
            ValueError: Raised if collection cannot be transformed to dict.

        Returns:
            Optional[Dict]: Collection as dict, or None if collection not found.
        """
        try:
            # Connect to STAC API and retrieve collection
            logger.info(f"Connecting to STAC API at {self.api_url}")
            client = Client.open(self.api_url)
            logger.debug(f"Fetching collection {self.collection_id}")
            collection = client.get_collection(self.collection_id)
        except APIError as e:
            # Check if this is a 404 error (collection not found)
            if hasattr(e, "status_code") and e.status_code == 404:
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
            raise ValueError(f"Failed to transform collection to dict: {str(e)}")

        logger.info(f"Successfully fetched collection {self.collection_id}")
        return collection_d

    def fetch_public_items(self) -> List[str]:
        """Get STAC Items in public catalog.

        Returns:
            List[str]: List of published item ids associated with collection.
        """
        try:
            # Connect to STAC API and retrieve items
            logger.info(f"Connecting to STAC API at {self.api_url}")
            client = Client.open(self.api_url)
            logger.debug(f"Fetching items for collection {self.collection_id}")
            items = client.get_collection(self.collection_id).get_items()

            # Get item ids from items
            item_ids = [item.id for item in items]

            return item_ids
        except Exception as e:
            logger.error(
                f"Failed to fetch items for collection {self.collection_id}: {str(e)}"
            )
            # Return empty list instead of None to avoid errors downstream
            return []

    def fetch_public_item(self, item_id: str) -> Optional[Dict]:
        """Get STAC Item in public catalog.

        Returns:
            Optional[Dict]: Item as dict, or None if item not found.
        """
        try:
            # Connect to STAC API and retrieve item
            logger.info(f"Connecting to STAC API at {self.api_url}")
            client = Client.open(self.api_url)
            logger.debug(f"Fetching item {item_id}")
            item = client.get_collection(self.collection_id).get_item(item_id)
        except APIError as e:
            # Check if this is a 404 error (item not found)
            if hasattr(e, "status_code") and e.status_code == 404:
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
            raise ValueError(f"Failed to transform item to dict: {str(e)}")

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
                raise ValueError("No local collection provided for comparison")

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

    def publish_to_catalog(self) -> STACReport:
        """Publish STAC Collection to public catalog."""
        try:
            logger.info(f"Publishing collection {self.collection_id} to catalog")
            if not self.collection:
                logger.error("No collection provided for publishing")
                raise ValueError("No collection provided for publishing")

            # Get STAC API key from environment variable
            stac_api_key = os.getenv("STAC_API_KEY")
            if not stac_api_key:
                logger.error("STAC_API_KEY environment variable is not set")
                raise ValueError("STAC_API_KEY environment variable is not set")

            # Create STAC report
            stac_report = STACReport(
                collection_id=self.collection_id,
                items=[],
                is_published=False,
                collection_url=f"{self.api_url}/collections/{self.collection_id}",
                error=None,
            )

            # Check if collection already exists
            try:
                existing_collection = self.fetch_public_collection()
            except APIError as e:
                # If we can't connect to the API, we can't publish
                logger.error(
                    f"Cannot publish collection {self.collection_id}: API is unavailable"
                )
                stac_report.error = STACError(
                    code="API_UNAVAILABLE",
                    message="STAC API is unavailable",
                    timestamp=datetime.now(tz=timezone.utc),
                    details={"error": str(e)},
                )
                return stac_report

            # Set up headers
            headers = {
                "Content-Type": "application/json",
                "D2S-STAC-API-Key": stac_api_key,
            }

            # Prepare collection data
            collection_data = self.collection.to_dict()

            if existing_collection:
                # Collection exists, use PUT to update
                logger.info(
                    f"Collection {self.collection_id} exists, updating with PUT"
                )
                endpoint = f"{self.api_url}/collections/{self.collection_id}"
                response = requests.put(endpoint, headers=headers, json=collection_data)
            else:
                # Collection doesn't exist, use POST to create
                logger.info(
                    f"Collection {self.collection_id} doesn't exist, creating with POST"
                )
                endpoint = f"{self.api_url}/collections"
                response = requests.post(
                    endpoint, headers=headers, json=collection_data
                )

            if response.status_code not in (200, 201):
                logger.error(
                    f"Failed to publish collection {self.collection_id}: {response.status_code} {response.text}"
                )
                stac_report.error = STACError(
                    code="PUBLISH_FAILED",
                    message="Failed to publish collection",
                    timestamp=datetime.now(tz=timezone.utc),
                    details={"error": response.text},
                )
                return stac_report

            # Update published status in report
            stac_report.is_published = True

            logger.info(f"Successfully published collection {self.collection_id}")

            # Get item ids from items
            public_item_ids = self.fetch_public_items()

            # Prepare items data
            items_data = [item.to_dict() for item in self.items]

            # Publish items to catalog
            for item in items_data:
                # Add item to report
                item_status = ItemStatus(
                    item_id=item["id"],
                    is_published=False,
                    item_url=f"{self.api_url}/collections/{self.collection_id}/items/{item['id']}",
                    error=None,
                )

                # Use FastAPI's jsonable_encoder to handle datetime objects
                jsonable_item = jsonable_encoder(item)
                if item["id"] not in public_item_ids:
                    logger.info(f"Publishing item {item['id']} to catalog")
                    endpoint = f"{self.api_url}/collections/{self.collection_id}/items"
                    response = requests.post(
                        endpoint, headers=headers, json=jsonable_item
                    )
                else:
                    # Update item if it already exists
                    logger.info(f"Updating item {item['id']} in catalog")
                    endpoint = f"{self.api_url}/collections/{self.collection_id}/items/{item['id']}"
                    response = requests.put(
                        endpoint, headers=headers, json=jsonable_item
                    )

                if response.status_code not in (200, 201):
                    logger.error(
                        f"Failed to publish item {item['id']}: {response.status_code} {response.text}"
                    )
                    item_status.error = STACError(
                        code="PUBLISH_FAILED",
                        message="Failed to publish item",
                        timestamp=datetime.now(tz=timezone.utc),
                        details={"error": response.text},
                    )
                    stac_report.items.append(item_status)
                    continue

                # Update item status in report
                item_status.is_published = True
                stac_report.items.append(item_status)

                logger.info(f"Successfully published item {item['id']}")

            return stac_report

        except Exception as e:
            logger.error(f"Failed to publish collection {self.collection_id}: {str(e)}")
            raise

    def remove_from_catalog(self) -> None:
        """Remove STAC Collection from public catalog."""
        try:
            logger.info(f"Removing collection {self.collection_id} from catalog")

            # Get STAC API key from environment variable
            stac_api_key = os.getenv("STAC_API_KEY")
            if not stac_api_key:
                logger.error("STAC_API_KEY environment variable is not set")
                raise ValueError("STAC_API_KEY environment variable is not set")

            # Set up headers
            headers = {
                "D2S-STAC-API-Key": stac_api_key,
            }

            # Use DELETE method with the collection-specific endpoint
            endpoint = f"{self.api_url}/collections/{self.collection_id}"
            response = requests.delete(endpoint, headers=headers)

            if response.status_code != 200:
                if response.status_code == 404:
                    logger.info(
                        f"Collection {self.collection_id} not found in STAC catalog"
                    )
                else:
                    logger.error(
                        f"Failed to remove collection {self.collection_id}: {response.status_code} {response.text}"
                    )
                    raise Exception(
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
            logger.debug(f"Checking if STAC API at {cls.STAC_API_URL} is available")
            response = requests.get(cls.STAC_API_URL, timeout=5)
            is_available = response.status_code == 200
            if not is_available:
                logger.warning(
                    f"STAC API at {cls.STAC_API_URL} returned status code {response.status_code}"
                )
            return is_available
        except requests.RequestException as e:
            logger.warning(f"STAC API at {cls.STAC_API_URL} is unavailable: {str(e)}")
            return False
