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
    ):
        self.db = db
        self.project_id = project_id
        self.sci_doi = sci_doi
        self.sci_citation = sci_citation
        self.license = (
            license or "CC-BY-NC-4.0"
        )  # Default to CC-BY-NC-4.0 if not provided
        self.custom_titles = custom_titles or {}

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
                    title = generate_item_title(
                        data_product, flight, self.custom_titles
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
        # Prepare scientific metadata
        stac_extensions = []
        extra_fields = {}

        # Add scientific extension if DOI or citation is provided
        if self.sci_doi or self.sci_citation:
            stac_extensions.append(SCIENTIFIC_EXTENSION_URI)
            if self.sci_doi:
                extra_fields["sci:doi"] = self.sci_doi
            if self.sci_citation:
                extra_fields["sci:citation"] = self.sci_citation

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
        flight_properties = {
            "data_product_details": {
                "data_type": data_product.data_type,
            },
            "flight_details": {
                "flight_id": str(flight.id),
                "acquisition_date": date_to_datetime(
                    flight.acquisition_date
                ).isoformat(),
                "altitude": flight.altitude,
                "forward_overlap": flight.forward_overlap,
                "side_overlap": flight.side_overlap,
                "platform": flight.platform,
                "sensor": flight.sensor,
            },
        }
        # Add title to properties - use custom title if provided, otherwise use default
        title = generate_item_title(data_product, flight, self.custom_titles)
        flight_properties["title"] = title

        if data_product.data_type == "point_cloud":
            # Create COPC item
            item = pdal_to_stac.create_item(
                path_to_copc=data_product.filepath,
                collection_id=collection_id,
                fallback_dt=date_to_datetime(flight.acquisition_date),
                flight_properties=flight_properties,
            )
        else:
            # Create STAC Asset for COG
            bbox, asset = generate_asset_for_cog(data_product.filepath)
            item = Item(
                id=str(data_product.id),
                collection=collection_id,
                geometry=bbox_to_geom(bbox),
                bbox=list(bbox),
                stac_extensions=COG_EXTENSIONS,
                datetime=date_to_datetime(flight.acquisition_date),
                properties={**flight_properties},
            )
            item.add_asset(key=str(data_product.id), asset=asset)

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
) -> str:
    """Generate title for a STAC item.

    Args:
        data_product: DataProduct object
        flight: Flight object
        custom_titles: Optional dict of custom titles keyed by data_product_id

    Returns:
        str: Generated title for the item
    """
    data_product_id = str(data_product.id)
    if (
        custom_titles
        and data_product_id in custom_titles
        and custom_titles[data_product_id]
    ):
        return custom_titles[data_product_id]
    else:
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
        media_type="image/tiff",
        extra_fields={**proj_info, **raster_info, **eo_info},
        roles=None,
    )

    return bbox, asset
