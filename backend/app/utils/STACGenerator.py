import logging
from datetime import date, datetime, timezone
from typing import List, Tuple, Optional

import geopandas as gpd
import rasterio
from pydantic import UUID4
from pystac import (
    Asset,
    Catalog,
    Collection,
    Extent,
    Item,
    SpatialExtent,
    TemporalExtent,
)
from rio_stac.stac import (
    bbox_to_geom,
    get_dataset_geom,
    get_eobands_info,
    get_projection_info,
    get_raster_info,
)
from rio_stac.stac import EO_EXT_VERSION, RASTER_EXT_VERSION, PROJECTION_EXT_VERSION
from sqlalchemy.orm import Session

from app import crud, models
from app.api.api_v1.endpoints.data_products import get_static_dir
from app.crud.crud_data_product import get_url
from app.utils import pdal_to_stac
from app.schemas import STACError, ItemStatus


logger = logging.getLogger("__name__")


COG_EXTENSIONS = [
    f"https://stac-extensions.github.io/projection/{PROJECTION_EXT_VERSION}/schema.json",
    f"https://stac-extensions.github.io/raster/{RASTER_EXT_VERSION}/schema.json",
    f"https://stac-extensions.github.io/eo/{EO_EXT_VERSION}/schema.json",
]

# Scientific extension URI
SCIENTIFIC_EXTENSION_URI = (
    "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
)


class STACGenerator:
    def __init__(
        self,
        db: Session,
        project_id: UUID4,
        sci_doi: Optional[str] = None,
        sci_citation: Optional[str] = None,
        license: Optional[str] = None,
        custom_titles: Optional[dict] = None,
        cached_stac_metadata: Optional[dict] = None,
    ):
        self.db = db
        self.project_id = project_id
        self.sci_doi = sci_doi
        self.sci_citation = sci_citation
        # Handle license with priority: new value, cached value, then default
        cached_license = None
        if (
            cached_stac_metadata
            and "collection" in cached_stac_metadata
            and isinstance(cached_stac_metadata["collection"], dict)
        ):
            cached_license = cached_stac_metadata["collection"].get("license")

        self.license = license or cached_license or "CC-BY-NC-4.0"
        self.custom_titles = custom_titles or {}
        self.cached_stac_metadata = cached_stac_metadata

        # Create a lookup dictionary for cached items by data product ID
        self.cached_items_lookup = {}
        if cached_stac_metadata and "items" in cached_stac_metadata:
            for item in cached_stac_metadata["items"]:
                self.cached_items_lookup[item["id"]] = item

        # Get project and flights associated with project
        self.project = self.get_project()
        self.flights = self.get_flights()

        # Create STAC Collection for project
        self.collection = self.generate_stac_collection()

        #  Iterate over each flight
        self.items: List[Item] = []
        self.failed_items: List[ItemStatus] = []
        for flight in self.flights:
            # Get data products associated with flight
            data_products = self.get_data_products(flight_id=flight.id)
            # Iterate over each data product
            for data_product in data_products:
                try:
                    # Create STAC Item for each data product
                    item = self.generate_stac_item(
                        collection_id=self.collection.id,
                        data_product=data_product,
                        flight=flight,
                    )
                    self.items.append(item)
                except Exception as e:
                    # Log the error and add to failed items list
                    error_msg = f"Failed to generate STAC item for data product {data_product.id}: {str(e)}"
                    logger.error(error_msg)

                    # Generate title for failed item using utility function
                    # Get cached item for this data product
                    data_product_id_str = str(data_product.id)
                    cached_item = self.cached_items_lookup.get(data_product_id_str)
                    title = generate_item_title(
                        data_product, flight, self.custom_titles, cached_item
                    )

                    # Create failed item status
                    failed_item = ItemStatus(
                        item_id=str(data_product.id),
                        is_published=False,
                        item_url=None,
                        error=STACError(
                            code="ITEM_GENERATION_FAILED",
                            message=str(e),
                            timestamp=datetime.now(tz=timezone.utc),
                            details={
                                "data_product_id": str(data_product.id),
                                "data_type": data_product.data_type,
                                "filepath": data_product.filepath,
                                "flight_id": str(flight.id),
                                "title": title,
                                "acquisition_date": str(flight.acquisition_date),
                                "platform": flight.platform,
                                "sensor": flight.sensor,
                            },
                        ),
                    )
                    self.failed_items.append(failed_item)

        # Raise exception if no data products were found at all
        if len(self.items) == 0 and len(self.failed_items) == 0:
            raise ValueError("No data products found in project.")

        # Add items to collection (only successful ones)
        if self.items:
            self.collection.add_items(self.items)

            # Create dummy catalog for validation
            catalog = Catalog(
                id="dummy-catalog", description="Dummy catalog for validation"
            )
            catalog.add_child(self.collection)
            catalog.normalize_hrefs("./")

    def get_project(self) -> models.Project:
        """Return project associated with "project_id" from database.

        Raises:
            ValueError: Raised if project cannot be found.

        Returns:
            models.Project: Project object.
        """
        project = crud.project.get(db=self.db, id=self.project_id)

        if not project:
            raise ValueError("Project not found")

        return project

    def get_flights(self) -> List[models.Flight]:
        """Return flights associated with project.

        Raises:
            ValueError: Raised if zero flights are found.

        Returns:
            List[models.Flight]: List of flight objects.
        """
        flights = crud.flight.get_multi_by_project_id(
            db=self.db, project_id=self.project_id
        )
        if len(flights) == 0:
            raise ValueError(
                "Project must have at least one flight with a data product to publish"
            )

        return list(flights)

    def get_data_products(self, flight_id: UUID4) -> List[models.DataProduct]:
        """Return data products associated with a flight.

        Args:
            flight_id (UUID4): Flight id.

        Raises:
            ValueError: Raised if flight not found.

        Returns:
            List[models.DataProduct]: _description_
        """
        flight = crud.flight.get(db=self.db, id=flight_id)

        if not flight:
            raise ValueError("Flight not found.")

        # Filter out deactivated data products
        return [dp for dp in flight.data_products if dp.is_active]

    def generate_stac_collection(self) -> Collection:
        """Create PySTAC Collection for project.

        Returns:
            Collection: Project Collection.
        """
        # Prepare scientific metadata with priority:
        # 1. New values from current request (self.sci_doi, self.sci_citation)
        # 2. Existing values from cached collection
        # 3. No scientific metadata
        stac_extensions = []
        extra_fields = {}

        # Get cached scientific metadata if available
        cached_sci_doi = None
        cached_sci_citation = None
        if (
            self.cached_stac_metadata
            and "collection" in self.cached_stac_metadata
            and isinstance(self.cached_stac_metadata["collection"], dict)
        ):
            cached_collection = self.cached_stac_metadata["collection"]
            cached_sci_doi = cached_collection.get("sci:doi")
            cached_sci_citation = cached_collection.get("sci:citation")

        # Determine final values: prioritize new values, then cached values
        final_sci_doi = self.sci_doi or cached_sci_doi
        final_sci_citation = self.sci_citation or cached_sci_citation

        # Add scientific extension if DOI or citation is provided
        if final_sci_doi or final_sci_citation:
            stac_extensions.append(SCIENTIFIC_EXTENSION_URI)
            if final_sci_doi:
                extra_fields["sci:doi"] = final_sci_doi
            if final_sci_citation:
                extra_fields["sci:citation"] = final_sci_citation

        collection = Collection(
            id=str(self.project.id),
            title=self.project.title,
            description=self.project.description,
            extent=Extent(
                spatial=self.get_spatial_extent(), temporal=self.get_temporal_extent()
            ),
            license=self.license,
            stac_extensions=stac_extensions if stac_extensions else None,
            extra_fields=extra_fields if extra_fields else None,
        )

        return collection

    def generate_stac_item(
        self,
        collection_id: str,
        data_product: models.DataProduct,
        flight: models.Flight,
    ) -> Item:
        data_product_id_str = str(data_product.id)

        # Check if we have cached data for this data product
        cached_item = self.cached_items_lookup.get(data_product_id_str)

        flight_details = {
            "flight_id": str(flight.id),
            "acquisition_date": date_to_datetime(flight.acquisition_date).isoformat(),
            "altitude": flight.altitude,
            "forward_overlap": flight.forward_overlap,
            "side_overlap": flight.side_overlap,
            "platform": flight.platform,
            "sensor": flight.sensor,
        }

        # Include flight name if provided
        if flight.name:
            flight_details["flight_name"] = flight.name

        flight_properties = {
            "data_product_details": {
                "data_type": data_product.data_type,
            },
            "flight_details": flight_details,
        }
        # Add title to properties - use custom title if provided, then cached title, otherwise use default
        title = generate_item_title(
            data_product, flight, self.custom_titles, cached_item
        )
        flight_properties["title"] = title

        if data_product.data_type == "point_cloud":
            # Create COPC item - pass cached item if available
            item = pdal_to_stac.create_item(
                path_to_copc=data_product.filepath,
                collection_id=collection_id,
                fallback_dt=date_to_datetime(flight.acquisition_date),
                flight_properties=flight_properties,
                item_id=data_product_id_str,
                cached_item=cached_item,
            )
        else:
            # Create STAC Asset for COG - use cached data if available
            if cached_item:
                # Use cached geometry, bbox, and asset
                geometry = cached_item["geometry"]
                bbox = cached_item["bbox"]
                # Get the cached asset (should be the first asset)
                cached_assets = cached_item.get("assets", {})
                if cached_assets:
                    # Get the first asset key and data
                    asset_key = list(cached_assets.keys())[0]
                    cached_asset_data = cached_assets[asset_key]
                    # Create asset from cached data
                    asset = Asset(
                        href=cached_asset_data["href"],
                        media_type=cached_asset_data.get(
                            "type",
                            "image/tiff; application=geotiff; profile=cloud-optimized",
                        ),
                        extra_fields={
                            k: v
                            for k, v in cached_asset_data.items()
                            if k not in ["href", "type"]
                        },
                        roles=cached_asset_data.get("roles"),
                    )
                else:
                    # Fallback to computing asset if no cached asset found
                    bbox, asset = generate_asset_for_cog(data_product.filepath)
                    geometry = bbox_to_geom(bbox)
            else:
                # No cached data, compute from scratch
                bbox, asset = generate_asset_for_cog(data_product.filepath)
                geometry = bbox_to_geom(bbox)

            item = Item(
                id=data_product_id_str,
                collection=collection_id,
                geometry=geometry,
                bbox=list(bbox),
                stac_extensions=COG_EXTENSIONS,
                datetime=date_to_datetime(flight.acquisition_date),
                properties={**flight_properties},
            )
            item.add_asset(key=data_product_id_str, asset=asset)

        # Log the title from properties instead
        logger.info(f"Item title: {item.properties.get('title', 'No title set')}")
        return item

    def get_spatial_extent(self) -> SpatialExtent:
        """Creates spatial extent for a STAC Collection using the bounding
        box extracted from a project boundary.

        Raises:
            ValueError: Raised if project boundary not found.
            e: Raised if unable to read project boundary geojson.

        Returns:
            SpatialExtent: Spatial extent for collection.
        """
        geojson = crud.location.get_geojson_location(
            db=self.db, location_id=self.project.location_id
        )
        if not geojson:
            raise ValueError("Project must have a boundary.")

        try:
            gdf = gpd.read_file(geojson.model_dump_json(), driver="GeoJSON")
            bounds = list(gdf.total_bounds)
        except Exception as e:
            logger.exception(e)
            raise e

        return SpatialExtent(bboxes=[bounds])

    def get_temporal_extent(self) -> TemporalExtent:
        """Creates a temporal extent for a STAC Collection, prioritizing the
        project start (planting_date) and end (harvest_date) dates, followed by
        the earliest and latest flight acquisition dates, and finally defaulting
        to today's date with no end date.

        Returns:
            TemporalExtent: Temporal extent for collecton.
        """
        if self.project.planting_date or self.project.harvest_date:
            p_date = (
                date_to_datetime(self.project.planting_date)
                if self.project.planting_date is not None
                else None
            )
            h_date = (
                date_to_datetime(self.project.harvest_date)
                if self.project.harvest_date is not None
                else None
            )
            temporal_extent = TemporalExtent(intervals=[[p_date, h_date]])
        elif len(self.flights) > 0:
            flights_sorted = sorted(
                self.flights,
                key=lambda flight: flight.acquisition_date,
            )
            temporal_extent = TemporalExtent(
                intervals=[
                    [
                        date_to_datetime(flights_sorted[0].acquisition_date),
                        date_to_datetime(flights_sorted[-1].acquisition_date),
                    ]
                ]
            )
        else:
            temporal_extent = TemporalExtent(
                intervals=[[datetime.now(tz=timezone.utc), None]]
            )

        return temporal_extent


def date_to_datetime(d: date) -> datetime:
    """Convert date object to datetime object with timezone awareness.

    Args:
        d (date): Date object.

    Returns:
        datetime: Timezone aware datetime object.
    """
    return datetime(d.year, d.month, d.day).replace(tzinfo=timezone.utc)


def generate_item_title(
    data_product: models.DataProduct,
    flight: models.Flight,
    custom_titles: Optional[dict] = None,
    cached_item: Optional[dict] = None,
) -> str:
    """Generate title for a STAC item.

    Priority order:
    1. Custom title from current request (custom_titles)
    2. Existing title from cached item (if not default pattern)
    3. Generated default title

    Args:
        data_product: DataProduct object
        flight: Flight object
        custom_titles: Optional dict of custom titles keyed by data_product_id
        cached_item: Optional cached STAC item data

    Returns:
        str: Generated title for the item
    """
    data_product_id = str(data_product.id)

    # 1. Check for new custom title from current request
    if (
        custom_titles
        and data_product_id in custom_titles
        and custom_titles[data_product_id]
    ):
        return custom_titles[data_product_id]

    # 2. Check for existing title in cached item
    if (
        cached_item
        and "properties" in cached_item
        and "title" in cached_item["properties"]
    ):
        cached_title = cached_item["properties"]["title"]
        # Generate default title to compare against
        default_title = f"{flight.acquisition_date}_{data_product.data_type}_{flight.sensor}_{flight.platform}"
        # If cached title is not the default pattern, preserve it
        if cached_title != default_title:
            return cached_title

    # 3. Generate default title
    return f"{flight.acquisition_date}_{data_product.data_type}_{flight.sensor}_{flight.platform}"


def generate_asset_for_cog(
    path_to_cog: str,
) -> Tuple[Tuple[float, float, float, float], Asset]:
    """Generate a STAC Asset for a COG.

    Args:
        path_to_cog (str): Path to COG.

    Returns:
        Tuple[Tuple[float, float, float, float], Asset]: Tuple containing the bounding box and the asset.
    """
    with rasterio.open(path_to_cog) as src:
        # Bounding box and footprint for COG
        bbox = get_dataset_geom(src)["bbox"]

        # Projection info
        proj_info = {
            f"proj:{name}": value for name, value in get_projection_info(src).items()
        }

        # Raster bands info
        raster_info = {"raster:bands": get_raster_info(src)}

        # Electro-optical info
        eo_info = {"eo:bands": get_eobands_info(src)}

        # Construct URL for COG
        cog_url = get_url(path_to_cog, get_static_dir())

    # Generate STAC Asset
    asset = Asset(
        href=cog_url,
        media_type="image/tiff; application=geotiff; profile=cloud-optimized",
        extra_fields={**proj_info, **raster_info, **eo_info},
        roles=["data"],
    )

    return bbox, asset
