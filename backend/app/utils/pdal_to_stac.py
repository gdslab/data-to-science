import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from osgeo import ogr, osr
from pystac import Asset, Item
import pdal

from app.api.api_v1.endpoints.data_products import get_static_dir
from app.crud.crud_data_product import get_url


osr.DontUseExceptions()

COPC_EXTENSIONS = ["https://stac-extensions.github.io/pointcloud/v1.0.0/schema.json"]


def validate_coordinate_system(path_to_copc: str) -> bool:
    """
    Validate if the point cloud has a valid coordinate system using pdal info --summary.
    This is a lightweight check that doesn't process all points.

    Args:
        path_to_copc: Path to the COPC file

    Returns:
        bool: True if the point cloud has a valid coordinate system, False otherwise
    """
    try:
        # Use pdal info --summary for lightweight metadata extraction
        result = subprocess.run(
            ["pdal", "info", "--summary", path_to_copc],
            capture_output=True,
            text=True,
            check=True,
        )

        info_data = json.loads(result.stdout)

        # Check if spatial reference exists and is not empty
        srs = info_data.get("summary", {}).get("srs", {})

        # Check for various SRS fields that indicate a valid coordinate system
        has_valid_srs = any(
            [srs.get("compoundwkt"), srs.get("wkt"), srs.get("proj4"), srs.get("units")]
        )

        return has_valid_srs

    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        # If pdal info fails or output is malformed, assume no valid SRS
        return False


def create_item(
    path_to_copc: str,
    collection_id: str,
    fallback_dt: datetime,
    flight_properties: Dict[str, Any],
) -> Item:
    # First, validate that the point cloud has a coordinate system
    if not validate_coordinate_system(path_to_copc):
        raise ValueError(
            f"Point cloud does not have a valid coordinate system and cannot be published to STAC"
        )

    # pdal info --all call references hexbin, stats, and info filters
    r = pdal.Reader.copc(path_to_copc)
    hb = pdal.Filter.hexbin()
    s = pdal.Filter.stats()
    i = pdal.Filter.info()

    pipeline: pdal.Pipeline = r | hb | s | i

    count = pipeline.execute()

    boundary = pipeline.metadata["metadata"][hb.type]
    stats = pipeline.metadata["metadata"][s.type]
    info = pipeline.metadata["metadata"][i.type]
    copc = pipeline.metadata["metadata"][r.type]

    # Create STAC Asset for COPC
    copc_url = get_url(path_to_copc, get_static_dir())
    asset = Asset(href=copc_url)

    # Get geometry from boundary if possible, fallback to stats bbox
    geometry = None

    try:
        geometry = convertGeometry(
            boundary["boundary_json"], copc["comp_spatialreference"]
        )
    except KeyError:
        geometry = stats["bbox"]["EPSG:4326"]["boundary"]
    finally:
        if not geometry:
            raise ValueError("Unable to find geometry")

    # Get bounding box
    bbox = None
    try:
        bbox = convertBBox(stats["bbox"]["EPSG:4326"]["bbox"])
    except KeyError:
        bbox = convertBBox(boundary["boundary_json"])
    finally:
        if not bbox:
            raise ValueError("Unable to find bounding box")

    # Unique UUID for COPC
    copc_uuid = Path(path_to_copc).stem.replace(".copc", "")

    # Extra properties for STAC Item
    try:
        properties = {
            "pc:count": count,
            "pc:density": boundary.get("avg_pt_per_sq_unit", 0),
            "pc:schemas": info["schema"]["dimensions"],
            "pc:statistics": stats["statistic"],
            "pc:type": "point_cloud",
            "datetime": capture_date(copc),
            "sensor_type": "flight.sensor",
        }
    except KeyError:
        raise ValueError("Unable to find properties")
    except Exception as e:
        raise ValueError(f"Error creating properties: {e}")

    # Create STAC Item for COPC
    item = Item(
        id=copc_uuid,
        collection=collection_id,
        geometry=geometry,
        bbox=bbox,
        stac_extensions=COPC_EXTENSIONS,
        datetime=fallback_dt,
        properties={**flight_properties, **properties},
    )
    item.add_asset(key=copc_uuid, asset=asset)

    return item


def capture_date(pdalinfo: Dict[str, Any]) -> str:
    year = pdalinfo["creation_year"]
    day = pdalinfo["creation_doy"]
    date = datetime(int(year), 1, 1) + timedelta(
        int(day) - 1 if int(day) > 1 else int(day)
    )
    return date.isoformat() + "Z"


def convertGeometry(geom: Dict[str, Any], srs: str) -> Dict:
    in_ref = osr.SpatialReference()
    in_ref.SetFromUserInput(srs)
    out_ref = osr.SpatialReference()
    out_ref.SetFromUserInput("EPSG:4326")

    g = ogr.CreateGeometryFromJson(json.dumps(geom))
    g.AssignSpatialReference(in_ref)
    g.TransformTo(out_ref)
    return json.loads(g.ExportToJson())


def convertBBox(obj: Dict[str, Any]) -> List[float]:
    output = []
    output.append(float(obj["minx"]))
    output.append(float(obj["miny"]))
    output.append(float(obj["minz"]))
    output.append(float(obj["maxx"]))
    output.append(float(obj["maxy"]))
    output.append(float(obj["maxz"]))
    return output
