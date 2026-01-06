"""STAC metadata caching utilities.

This module provides helper classes for managing cached STAC metadata to avoid
expensive recomputation of geometry, assets, and properties.
"""

from typing import Optional, Tuple, List


class CachedSTACMetadata:
    """Helper class to encapsulate STAC metadata caching logic.

    This class provides a clean interface for accessing cached STAC metadata,
    avoiding expensive recomputation of geometry, assets, and properties.

    The cache structure is expected to be:
    {
        "collection": {
            "license": str,
            "sci:doi": str (optional),
            "sci:citation": str (optional),
            ...
        },
        "items": [
            {
                "id": str (data_product_id),
                "geometry": dict,
                "bbox": list,
                "assets": dict,
                "properties": dict,
                ...
            },
            ...
        ]
    }
    """

    def __init__(self, cached_stac_metadata: Optional[dict] = None):
        """Initialize cache with optional cached metadata.

        Args:
            cached_stac_metadata: Optional dictionary containing cached STAC data
                with 'collection' and 'items' keys
        """
        self._cache = cached_stac_metadata or {}
        self._items_lookup = self._build_items_lookup()

    def _build_items_lookup(self) -> dict:
        """Build lookup dictionary for cached items by data product ID.

        Returns:
            Dictionary mapping data product IDs to cached item data
        """
        items_lookup = {}
        if "items" in self._cache:
            for item in self._cache["items"]:
                items_lookup[item["id"]] = item
        return items_lookup

    def has_cache(self) -> bool:
        """Check if any cached metadata exists.

        Returns:
            True if cache contains data, False otherwise
        """
        return bool(self._cache)

    def get_license(self) -> Optional[str]:
        """Extract license from cached collection metadata.

        Returns:
            License identifier if found in cache, None otherwise
        """
        if not self._cache:
            return None

        collection = self._cache.get("collection")
        if not collection or not isinstance(collection, dict):
            return None

        return collection.get("license")

    def get_scientific_metadata(self) -> Tuple[Optional[str], Optional[str]]:
        """Extract scientific DOI and citation from cached collection.

        Returns:
            Tuple of (doi, citation), both can be None if not cached
        """
        if not self._cache:
            return None, None

        collection = self._cache.get("collection")
        if not collection or not isinstance(collection, dict):
            return None, None

        doi = collection.get("sci:doi")
        citation = collection.get("sci:citation")

        return doi, citation

    def get_contact_metadata(self) -> Tuple[Optional[str], Optional[str]]:
        """Extract contact name and email from cached collection.

        Returns:
            Tuple of (name, email), both can be None if not cached
        """
        if not self._cache:
            return None, None

        collection = self._cache.get("collection")
        if not collection or not isinstance(collection, dict):
            return None, None

        # Extract from contacts array if present
        contacts = collection.get("contacts")
        if not contacts or not isinstance(contacts, list) or len(contacts) == 0:
            return None, None

        # Get first contact
        contact = contacts[0]
        if not isinstance(contact, dict):
            return None, None

        name = contact.get("name")

        # Extract email from emails array
        email = None
        emails = contact.get("emails")
        if emails and isinstance(emails, list) and len(emails) > 0:
            email_obj = emails[0]
            if isinstance(email_obj, dict):
                email = email_obj.get("value")

        return name, email

    def get_item(self, data_product_id: str) -> Optional[dict]:
        """Get cached item data for a specific data product.

        Args:
            data_product_id: Data product ID (as string)

        Returns:
            Cached item dictionary if found, None otherwise
        """
        return self._items_lookup.get(data_product_id)

    def has_item(self, data_product_id: str) -> bool:
        """Check if cached item exists for a specific data product.

        Args:
            data_product_id: Data product ID (as string)

        Returns:
            True if cached item exists, False otherwise
        """
        return data_product_id in self._items_lookup

    def get_item_geometry(self, data_product_id: str) -> Optional[dict]:
        """Get cached geometry for a specific data product.

        Args:
            data_product_id: Data product ID (as string)

        Returns:
            Geometry dictionary if found in cache, None otherwise
        """
        item = self.get_item(data_product_id)
        return item.get("geometry") if item else None

    def get_item_bbox(self, data_product_id: str) -> Optional[list]:
        """Get cached bounding box for a specific data product.

        Args:
            data_product_id: Data product ID (as string)

        Returns:
            Bounding box list if found in cache, None otherwise
        """
        item = self.get_item(data_product_id)
        return item.get("bbox") if item else None

    def get_item_assets(self, data_product_id: str) -> Optional[dict]:
        """Get cached assets for a specific data product.

        Args:
            data_product_id: Data product ID (as string)

        Returns:
            Assets dictionary if found in cache, None otherwise
        """
        item = self.get_item(data_product_id)
        return item.get("assets") if item else None

    def get_item_properties(self, data_product_id: str) -> Optional[dict]:
        """Get cached properties for a specific data product.

        Args:
            data_product_id: Data product ID (as string)

        Returns:
            Properties dictionary if found in cache, None otherwise
        """
        item = self.get_item(data_product_id)
        return item.get("properties") if item else None

    def get_item_title(self, data_product_id: str) -> Optional[str]:
        """Get cached title for a specific data product.

        Args:
            data_product_id: Data product ID (as string)

        Returns:
            Title string if found in cached properties, None otherwise
        """
        properties = self.get_item_properties(data_product_id)
        return properties.get("title") if properties else None

    def get_raw_data_link_ids(self) -> List[str]:
        """Extract list of item IDs that have derived_from links in cache.

        This identifies which items previously had raw data links enabled
        by checking for the presence of derived_from links.

        Returns:
            List of data product IDs (as strings) that have derived_from links
        """
        item_ids_with_links = []

        if "items" in self._cache:
            for item in self._cache["items"]:
                # Check if item has links array
                if "links" in item and isinstance(item["links"], list):
                    # Check if any link has rel="derived_from"
                    has_derived_from = any(
                        link.get("rel") == "derived_from" for link in item["links"]
                    )
                    if has_derived_from:
                        item_ids_with_links.append(item["id"])

        return item_ids_with_links
