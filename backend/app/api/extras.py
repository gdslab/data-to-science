# extras.py
from typing import Any, Optional, Tuple
import logging
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import UUID4
from pyproj import CRS, Transformer
from sqlalchemy.orm import Session
import laspy
import pdal
import numpy as np

# Your app imports
from app import crud
from app.api import deps
from app.api.utils import get_copc_z_unit
from app.core.config import settings


extra_router = APIRouter()

logger = logging.getLogger(__name__)


@extra_router.get("/sl/{short_id}")
async def redirect_short_url(short_id: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Redirects to the original URL based on the provided short ID.
    """
    shortened_url = crud.shortened_url.get_by_short_id(db, short_id=short_id)
    if not shortened_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    original_url = shortened_url.original_url

    return RedirectResponse(
        url=original_url,
        status_code=303,
    )


def pdal_percentile_z(
    copc_path: str, pct: int = 2, decimation: int = 1000
) -> Optional[float]:
    """Calculate the Z-coordinate percentile from a COPC point cloud file.

    This function reads a Cloud Optimized Point Cloud (COPC) file using PDAL,
    applies decimation to reduce the point density for performance, and then
    calculates the specified percentile of the Z (elevation) values. This is
    commonly used for ground level estimation or terrain analysis.

    The function implements a fallback strategy: if the initial decimation results
    in fewer than 5000 points, it will retry with a lower decimation step (500)
    to get more points for a more accurate percentile calculation.

    Args:
        copc_path (str): Path to the COPC file to process
        pct (int, optional): Percentile to calculate (0-100). Lower values
            (e.g., 2) are useful for finding ground level. Defaults to 2.
        decimation (int, optional): Decimation step size - keep every Nth point
            (e.g., 1000 means keep every 1000th point). Higher values process faster
            but with less precision. Defaults to 1000.

    Returns:
        Optional[float]: The Z-coordinate value at the specified percentile,
            or None if the file contains no points or produces insufficient data
            even with reduced decimation.
    """
    # Check if the percentile z has been cached
    copc_dir = os.path.dirname(copc_path)
    percentile_z_cache_path = os.path.join(
        copc_dir, f"percentile_z_{pct}_{decimation}.txt"
    )
    if os.path.exists(percentile_z_cache_path):
        with open(percentile_z_cache_path, "r") as f:
            return float(f.read())

    # Try with the provided decimation first, then fallback to 500 if needed
    decimation_steps = [decimation] if decimation <= 500 else [decimation, 500]

    for current_decimation in decimation_steps:
        # Create PDAL pipeline configuration
        # First stage: read the COPC file with limits to control memory usage
        # Second stage: apply decimation to reduce point density for performance
        pipeline = {
            "pipeline": [
                {
                    "type": "readers.copc",
                    "filename": copc_path,
                    "resolution": 2.0,
                    "count": 200000,
                },
                {"type": "filters.decimation", "step": current_decimation},
            ]
        }

        # Create and execute the PDAL pipeline
        p = pdal.Pipeline(json.dumps(pipeline))
        p.execute()

        # Get the point cloud data as a numpy array
        arr = p.arrays[0]

        # Check if any points were read from the file
        if arr.size == 0:
            continue  # Try next decimation step if available

        # If we have sufficient points (>=5000) or this is our last attempt, proceed
        if arr.size >= 5000 or current_decimation == decimation_steps[-1]:
            # Need at least some points to calculate percentile
            if arr.size == 0:
                return None

            # Calculate and return the specified percentile of Z values
            percentile_z = float(np.percentile(arr["Z"], pct))
            with open(percentile_z_cache_path, "w") as f:
                f.write(str(percentile_z))
            return percentile_z

    # If we get here, all attempts failed
    return None


def probe_crs_and_center(
    copc_path: str,
) -> Tuple[
    Optional[str], Optional[Tuple[float, float, float]], Optional[str], Optional[str]
]:
    """
    Attempt to read the COPC's CRS and compute a geographic center for Cesium.

    Returns:
      proj4_str: str | None          -> proj4 for the source CRS (for proj4js)
      geo_center: (lon, lat, z) | None  -> center in EPSG:4326 degrees + meters height
      diag: str | None               -> diagnostic message (for logging / UI)
      z_unit: str | None             -> unit of the Z-axis
    """
    if laspy is None or CRS is None or Transformer is None:
        return None, None, "Missing laspy/pyproj on server", None

    try:
        with laspy.open(copc_path) as f:
            hdr = f.header
            crs = hdr.parse_crs()  # pyproj.CRS or None

            if crs is None:
                return None, None, "No CRS in COPC header", None

            # Center from header mins/maxs (no point read required)
            x0, y0, z0 = hdr.mins
            x1, y1, z1 = hdr.maxs
            cx = (x0 + x1) / 2.0
            cy = (y0 + y1) / 2.0
            cz = (z0 + z1) / 2.0

            # Transform to WGS84 lon/lat (+ keep Z as-is; note height datum caveat)
            wgs84 = CRS.from_epsg(4326)
            to_geo = Transformer.from_crs(crs, wgs84, always_xy=True)
            lon, lat, h = to_geo.transform(cx, cy, cz)

            proj4_str = crs.to_proj4()

            z_unit = get_copc_z_unit(crs)
            if z_unit == "foot" or z_unit == "ft" or z_unit == "feet":
                h = h * 0.3048

            return proj4_str, (lon, lat, h), None, z_unit
    except Exception as exc:
        return None, None, f"CRS probe failed: {exc}", None


def generate_potree_viewer_html(
    copc_path: str,
    is_mobile: bool,
) -> str:
    """
    Generate the HTML content for the Potree + optional Cesium viewer.

    Args:
        copc_path: Path to the COPC file
        is_mobile: Whether the viewer is on a mobile device

    Returns:
        HTML content as string
    """
    # Probe the CRS and dataset geographic center
    proj4_str, geo_center, diag, z_unit = probe_crs_and_center(
        copc_path.replace(settings.API_DOMAIN, "")
    )
    has_crs = proj4_str is not None and geo_center is not None

    if geo_center:
        initial_lon, initial_lat, initial_h = geo_center
    else:
        initial_lon = 0.0
        initial_lat = 0.0
        initial_h = 0.0

    # Serialize values safely for embedding
    JS_HAS_CRS = "true" if has_crs else "false"
    JS_PROJ4 = json.dumps(proj4_str or "")
    JS_INIT_LON = f"{initial_lon:.10f}"
    JS_INIT_LAT = f"{initial_lat:.10f}"
    JS_INIT_H = f"{initial_h:.3f}"
    JS_DIAG = json.dumps(diag or "")
    JS_IS_MOBILE = "true" if is_mobile else "false"
    JS_Z_UNIT_FACTOR = (
        "0.3048"
        if z_unit and any(unit in z_unit for unit in ["ft", "foot", "feet"])
        else "1.0"
    )

    # Compute z_low (try PDAL; optionally fall back to LAS header mins)
    z_low = None
    try:
        z_low = pdal_percentile_z(
            copc_path.replace(settings.API_DOMAIN, ""), pct=2, decimation=50
        )
    except Exception:
        logger.warning("Failed to compute z_low using pdal percentile z")

    # Fallback using laspy header mins[2] if you have local file access
    if z_low is None:
        try:
            import laspy

            # Extract local path from URL - keep everything from /static/projects onward
            if "/static/projects" in copc_path:
                local_path = copc_path.split("/static/projects", 1)[1]
                local_path = "/static/projects" + local_path
            else:
                local_path = copc_path

            with laspy.open(local_path) as f:
                z_low = float(f.header.mins[2])
        except Exception:
            pass

    JS_Z_LOW = "null" if z_low is None else f"{z_low:.3f}"

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0"
    />

    <link rel="stylesheet" type="text/css" href="/potree/libs/potree/potree.css" />
    <link rel="stylesheet" type="text/css" href="/potree/libs/jquery-ui/jquery-ui.min.css" />
    <link rel="stylesheet" type="text/css" href="/potree/libs/openlayers3/ol.css" />
    <link rel="stylesheet" type="text/css" href="/potree/libs/spectrum/spectrum.css" />
    <link rel="stylesheet" type="text/css" href="/potree/libs/jstree/themes/mixed/style.css" />
    <link rel="stylesheet" type="text/css" href="/potree/libs/Cesium/Widgets/CesiumWidget/CesiumWidget.css" />

    <style>
      body {{
        margin: 0;
        padding: 0;
        overflow: hidden;
        touch-action: manipulation;
        user-select: none;
        -webkit-user-select: none;
        -webkit-touch-callout: none;
      }}
      .potree_container {{
        width: 100%;
        height: 100vh;
        min-height: 300px;
        overflow: hidden;
      }}
      #potree_render_area {{
        width: 100%;
        height: 100%;
        min-height: inherit;
      }}
      /* When Cesium is disabled, use solid background to hide sidebar */
      body:not(.cesium-enabled) #potree_render_area {{
        background: #2a2a2a;
      }}
      #potree_render_area, #potree_render_area canvas {{
        touch-action: none;
        outline: none;
        user-select: none;
        cursor: crosshair;
        z-index: 1;
        background: transparent;
      }}
      #cesiumContainer {{
        position: absolute;
        width: 100%;
        height: 100%;
        inset: 0;
        background: #000;
        z-index: 0;
      }}
      #potree_toolbar {{
        position: absolute;
        z-index: 10000;
        left: 100px;
        top: 0px;
        background: black;
        color: white;
        padding: 0.3em 0.8em;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;
        border-radius: 0 0 0.3em 0.3em;
        display: flex;
        flex-wrap: wrap;
        max-width: calc(100vw - 120px);
      }}
      .potree_toolbar_label {{
        text-align: center;
        font-size: smaller;
        opacity: 0.9;
      }}
      .potree_toolbar_separator {{
        background: white;
        padding: 0;
        margin: 5px 10px;
        width: 1px;
      }}
      .loading-indicator {{
        position: absolute;
        top: 12px;
        right: 12px;
        background: rgba(0,0,0,0.7);
        color: white;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 13px;
        z-index: 20000;
      }}
      .notice {{
        position: absolute;
        z-index: 20001;
        left: 12px;
        bottom: 12px;
        background: rgba(0,0,0,0.65);
        color: #fff;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 12px;
        max-width: 32rem;
        line-height: 1.3;
      }}
      @media (max-width: 768px) {{
        #potree_toolbar {{
          left: 60px;
          top: 10px;
          font-size: 12px;
          padding: 0.2em 0.5em;
          max-width: calc(100vw - 80px);
        }}
        .annotation-action-icon {{
          width: 1.5em !important;
          height: auto !important;
        }}
      }}
    </style>

    <base target="_blank" />
  </head>
  <body>
    <div id="loading" class="loading-indicator">Loading point cloud...</div>

    <script>
      // Server-provided flags and values
      const PC_HAS_CRS = {JS_HAS_CRS};
      const PC_PROJ4 = {JS_PROJ4};
      const PC_INIT_LON = {JS_INIT_LON};
      const PC_INIT_LAT = {JS_INIT_LAT};
      const PC_INIT_H = {JS_INIT_H};
      const PC_DIAG = {JS_DIAG};
      const PC_IS_MOBILE = {JS_IS_MOBILE};
      const PC_Z_LOW = {JS_Z_LOW};
      const PC_Z_UNIT_FACTOR = {JS_Z_UNIT_FACTOR};
    </script>

    <script src="/potree/libs/jquery/jquery-3.1.1.min.js"></script>
    <script src="/potree/libs/spectrum/spectrum.js"></script>
    <script src="/potree/libs/jquery-ui/jquery-ui.min.js"></script>
    <script src="/potree/libs/other/BinaryHeap.js"></script>
    <script src="/potree/libs/tween/tween.min.js"></script>
    <script src="/potree/libs/d3/d3.js"></script>
    <script src="/potree/libs/proj4/proj4.js"></script>
    <script src="/potree/libs/openlayers3/ol.js"></script>
    <script src="/potree/libs/i18next/i18next.js"></script>
    <script src="/potree/libs/jstree/jstree.js"></script>
    <script src="/potree/libs/copc/index.js"></script>
    <script src="/potree/libs/potree/potree.js"></script>
    <script src="/potree/libs/plasio/js/laslaz.js"></script>
    <script src="/potree/libs/Cesium/Cesium.js"></script>

    <div class="potree_container">
      <div id="potree_render_area">
        <div id="potree_toolbar"></div>
        <div id="cesiumContainer" style="display: none;"></div>
      </div>
      <div id="potree_sidebar_container"></div>
    </div>

    <script type="module">
      import * as THREE from "/potree/libs/three.js/build/three.module.js";

      // Simple WebGL check
      (function checkWebGL() {{
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) {{
          const el = document.getElementById('loading');
          if (el) {{
            el.textContent = 'WebGL not supported';
            el.style.background = 'rgba(255,0,0,0.8)';
          }}
        }}
      }})();

      // Potree viewer
      window.viewer = new Potree.Viewer(document.getElementById("potree_render_area"));
      viewer.setEDLEnabled(true);
      viewer.setPointBudget(2_000_000);
      viewer.useHQ = true;
      viewer.setFOV(60);
      viewer.loadSettingsFromURL();
      viewer.setControls(viewer.earthControls);
      viewer.setBackground(null);
      viewer.renderer.setClearColor(0x000000, 0.0);
      viewer.renderer.domElement.style.background = "transparent";

      // GUI
      viewer.loadGUI(() => {{
        viewer.setLanguage('en');
        $("#menu_tools").next().show();
      }});

      // If we have a CRS, show Cesium and wire up transforms
      let cesiumViewer = null;
      if (PC_HAS_CRS && PC_PROJ4) {{
        // Add class to indicate Cesium is enabled
        document.body.classList.add('cesium-enabled');
        
        // Reveal Cesium container
        document.getElementById('cesiumContainer').style.display = 'block';

        // Start Cesium
        cesiumViewer = new Cesium.Viewer('cesiumContainer', {{
          useDefaultRenderLoop: false,
          animation: false,
          baseLayerPicker: false,
          fullscreenButton: false,
          geocoder: false,
          homeButton: false,
          infoBox: false,
          sceneModePicker: false,
          selectionIndicator: false,
          timeline: false,
          navigationHelpButton: false,
          imageryProvider: Cesium.createOpenStreetMapImageryProvider({{ url: 'https://a.tile.openstreetmap.org/' }}),
          terrainShadows: Cesium.ShadowMode.DISABLED
        }});

        // Define transforms using proj4js
        const mapProjection = proj4.defs("WGS84"); // lon/lat degrees
        window.toMap = proj4(PC_PROJ4, mapProjection);
        window.toScene = proj4(mapProjection, PC_PROJ4);

        // Place Cesium camera near dataset center
        const dst = Cesium.Cartesian3.fromDegrees(PC_INIT_LON, PC_INIT_LAT, PC_INIT_H);
        cesiumViewer.camera.setView({{
          destination: dst,
          orientation: {{
            heading: 10,
            pitch: -Cesium.Math.PI_OVER_TWO * 0.5,
            roll: 0.0
          }}
        }});
      }} else {{
        // No CRS → show a small notice
        const n = document.createElement('div');
        n.className = 'notice';
        n.textContent = PC_DIAG ? ('Basemap disabled: ' + PC_DIAG) : 'Basemap disabled: no CRS detected in point cloud';
        document.body.appendChild(n);
      }}

      // Load point cloud
      const path = "{copc_path}";
      Potree.loadPointCloud(path, "PointCloud", function(e) {{
        try {{
          if (e.type === 'loading_failed') {{
            throw new Error('Failed to load point cloud: ' + (e.message || 'Unknown error'));
          }}
          const pointcloud = e.pointcloud;
          if (!pointcloud) {{
            throw new Error('Point cloud object is null');
          }}
          viewer.scene.addPointCloud(pointcloud);

          const material = pointcloud.material;
          material.size = 1;
          material.pointSizeType = Potree.PointSizeType.ADAPTIVE;
          material.shape = Potree.PointShape.CIRCLE;

          viewer.fitToScreen(0.6);

          // Done loading
          const loadingEl = document.getElementById('loading');
          if (loadingEl) loadingEl.remove();
        }} catch (err) {{
          console.error('Point cloud loading error:', err);
          const loadingEl = document.getElementById('loading');
          if (loadingEl) {{
            loadingEl.textContent = 'Error loading point cloud: ' + err.message;
            loadingEl.style.background = 'rgba(255,0,0,0.8)';
          }}
        }}
      }});

      // Render loop with optional Cesium sync (only when toMap exists)
      function loop(timestamp) {{
        requestAnimationFrame(loop);

        viewer.update(viewer.clock.getDelta(), timestamp);
        viewer.render();

        if (typeof window.toMap !== 'undefined' && cesiumViewer) {{
          const camera = viewer.scene.getActiveCamera();

          const pPos    = new THREE.Vector3(0, 0, 0).applyMatrix4(camera.matrixWorld);
          const pRight  = new THREE.Vector3(600, 0, 0).applyMatrix4(camera.matrixWorld);
          const pUp     = new THREE.Vector3(0, 600, 0).applyMatrix4(camera.matrixWorld);
          const pTarget = viewer.scene.view.getPivot();

          const EPSILON = 0.5;
          window.PC_VERT_OFFSET_M = (typeof PC_Z_LOW === 'number') ? -(PC_Z_LOW * PC_Z_UNIT_FACTOR) + EPSILON : 0;

          const toCes = (pos) => {{
            const xy = [pos.x, pos.y];
            const height = (pos.z * PC_Z_UNIT_FACTOR) + (window.PC_VERT_OFFSET_M || 0);
            const deg = window.toMap.forward(xy); // [lon, lat]
            return Cesium.Cartesian3.fromDegrees(...deg, height);
          }};

          const cPos      = toCes(pPos);
          const cUpTarget = toCes(pUp);
          const cTarget   = toCes(pTarget);

          let cDir = Cesium.Cartesian3.subtract(cTarget, cPos, new Cesium.Cartesian3());
          let cUp  = Cesium.Cartesian3.subtract(cUpTarget, cPos, new Cesium.Cartesian3());

          cDir = Cesium.Cartesian3.normalize(cDir, new Cesium.Cartesian3());
          cUp  = Cesium.Cartesian3.normalize(cUp, new Cesium.Cartesian3());

          cesiumViewer.camera.setView({{
            destination: cPos,
            orientation: {{
              direction: cDir,
              up: cUp
            }}
          }});

          // Match FOV
          const aspect = viewer.scene.getActiveCamera().aspect;
          const fovy = Math.PI * (viewer.scene.getActiveCamera().fov / 180);
          if (aspect < 1) {{
            cesiumViewer.camera.frustum.fov = fovy;
          }} else {{
            const fovx = Math.atan(Math.tan(0.5 * fovy) * aspect) * 2;
            cesiumViewer.camera.frustum.fov = fovx;
          }}

          cesiumViewer.render();
        }}
      }}
      requestAnimationFrame(loop);
    </script>

    <script type="module">
        import * as THREE from "/potree/libs/three.js/build/three.module.js";

        // source: https://github.com/potree/potree/blob/develop/examples/toolbar.html
        
        // HTML
        const elToolbar = $("#potree_toolbar");
        elToolbar.html(`
          <span>
            <div class="potree_toolbar_label">
				      Attribute
			      </div>
			      <div>
				      <img name="action_elevation" src="/potree/resources/icons/profile.svg" class="annotation-action-icon" style="width: 2em; height: auto;"/>
				      <img name="action_rgb" src="/potree/resources/icons/rgb.svg" class="annotation-action-icon" style="width: 2em; height: auto;"/>
			      </div>
          </span>
          
          <span class="potree_toolbar_separator" />
        
          <span>
            <div class="potree_toolbar_label">
              Gradient
            </div>
			      <div>
				      <span name="gradient_schemes"></span>
			      </div>
		      </span>

          <span class="potree_toolbar_separator" />

		      <span>
			      <div class="potree_toolbar_label">
				      Measure
			      </div>
			      <div>
				      <img name="action_measure_point" src="/potree/resources/icons/point.svg" class="annotation-action-icon" style="width: 2em; height: auto;"/>
				      <img name="action_measure_distance" src="/potree/resources/icons/distance.svg" class="annotation-action-icon" style="width: 2em; height: auto;"/>
				      <img name="action_measure_circle" src="/potree/resources/icons/circle.svg" class="annotation-action-icon" style="width: 2em; height: auto;"/>
			      </div>
		      </span>

          <span class="potree_toolbar_separator" />

          <span>
            <div class="potree_toolbar_label" style="width: 12em">
              Material
            </div>
            <div>
              <select id="optMaterial" name="optMaterial"></select>
            </div>
          </span>

          <span class="potree_toolbar_separator" />

          <span>
            <div class="potree_toolbar_label">
              <span data-i18n="appearance.nb_max_pts">Point Budget</span>: 
              <span name="lblPointBudget" style="display: inline-block; width: 4em;"></span>
            </div>
            <div>
              <div id="sldPointBudget"></div>
            </div>
          </span>

        `);

        // CONTENT & ACTIONS
        {{// ATTRIBUTE
          elToolbar.find("img[name=action_elevation]").click( () => {{
            viewer.scene.pointclouds.forEach( pc => pc.material.activeAttributeName = "elevation" );
          }});
      
          elToolbar.find("img[name=action_rgb]").click( () => {{
            viewer.scene.pointclouds.forEach( pc => pc.material.activeAttributeName = "rgba" );
          }});
        }}

        {{// GRADIENT
          const schemes = Object.keys(Potree.Gradients).map(name => ({{name: name, values: Potree.Gradients[name]}}));
          const elGradientSchemes = elToolbar.find("span[name=gradient_schemes]");
      
          for(const scheme of schemes){{
            const elButton = $(`
              <span style=""></span>
            `);
      
            const svg = Potree.Utils.createSvgGradient(scheme.values);
            svg.setAttributeNS(null, "class", `button-icon`);
            svg.style.height = "2em";
            svg.style.width = "1.3em";
      
            elButton.append($(svg));
      
            elButton.click( () => {{
              for(const pointcloud of viewer.scene.pointclouds){{
                pointcloud.material.activeAttributeName = "elevation";
                pointcloud.material.gradient = Potree.Gradients[scheme.name];
              }}
            }});
      
            elGradientSchemes.append(elButton);
          }}
        }}
      
        {{// MEASURE
          elToolbar.find("img[name=action_measure_point]").click( () => {{
            const measurement = viewer.measuringTool.startInsertion({{
              showDistances: false,
              showAngles: false,
              showCoordinates: true,
              showArea: false,
              closed: true,
              maxMarkers: 1,
              name: 'Point'
            }});
          }});
      
          elToolbar.find("img[name=action_measure_distance]").click( () => {{
            const measurement = viewer.measuringTool.startInsertion({{
              showDistances: true,
              showArea: false,
              closed: false,
              name: 'Distance'
            }});
          }});
      
          elToolbar.find("img[name=action_measure_circle]").click( () => {{
            const measurement = viewer.measuringTool.startInsertion({{
              showDistances: false,
              showHeight: false,
              showArea: false,
              showCircle: true,
              showEdges: false,
              closed: false,
              maxMarkers: 3,
              name: 'Circle'
            }});
          }}); 
        }}
      
        {{// MATERIAL
          let options = [
            "rgba", 
            "elevation",
            "level of detail",
            "indices",
            "intensity",
            "classification",
            // "source id",
          ];
      
          let attributeSelection = elToolbar.find('#optMaterial');
          for(let option of options){{
            let elOption = $(`<option>${{option}}</option>`);
            attributeSelection.append(elOption);
          }}
      
          const updateMaterialSelection = (event, ui) => {{
            let selectedValue = attributeSelection.selectmenu().val();
      
            for(const pointcloud of viewer.scene.pointclouds){{
              pointcloud.material.activeAttributeName = selectedValue;
            }}
          }};
      
          attributeSelection.selectmenu({{change: updateMaterialSelection}});
        }}
      
        {{// POINT BUDGET
          const minBudget = PC_IS_MOBILE ? 50_000 : 100_000;
          const maxBudget = PC_IS_MOBILE ? 1_000_000 : 2_000_000;
          const stepBudget = PC_IS_MOBILE ? 50_000 : 100_000;
          
          elToolbar.find('#sldPointBudget').slider({{
            value: viewer.getPointBudget(),
            min: minBudget,
            max: maxBudget,
            step: stepBudget,
            slide: (event, ui) => {{ viewer.setPointBudget(ui.value); }}
          }});
      
          const onBudgetChange = () => {{
            let budget = (viewer.getPointBudget() / (1000_000)).toFixed(1) + "M";
            elToolbar.find('span[name=lblPointBudget]').html(budget);
          }};
      
          onBudgetChange();
          viewer.addEventListener("point_budget_changed", onBudgetChange);
        }}
      </script>
  </body>
</html>"""


@extra_router.get("/potree-viewer", response_class=HTMLResponse)
async def get_potree_viewer(
    copc_path: str = Query(..., description="Path to the COPC file"),
    is_mobile: bool = Query(
        ...,
        description="Whether the viewer is on a mobile device",
    ),
) -> HTMLResponse:
    """
    Serves the Potree + optional Cesium viewer HTML content dynamically.

    Behavior:
      - If COPC has a CRS, enable Cesium and camera sync, and inject the proj4 string + WGS84 center.
      - If no CRS, disable Cesium and show Potree-only with a gentle banner.
    """
    html_content = generate_potree_viewer_html(copc_path, is_mobile)
    return HTMLResponse(content=html_content)


@extra_router.get("/share-potree-viewer", response_class=HTMLResponse)
async def get_share_potree_viewer(
    file_id: UUID4 = Query(..., description="ID of the data product file"),
    is_mobile: bool = Query(
        ...,
        description="Whether the viewer is on a mobile device",
    ),
    db: Session = Depends(deps.get_db),
    current_user: Optional[Any] = Depends(deps.get_optional_current_user),
) -> HTMLResponse:
    """
    Serves the Potree + optional Cesium viewer HTML content for shared data products.

    This endpoint accepts a file_id and uses CRUD operations to retrieve the data product
    and extract the COPC path, then generates the same viewer HTML as the regular potree-viewer.

    Access Control:
      - If data product is public: accessible to anyone
      - If data product is private: accessible only to authenticated users who are project members
      - Uses the same access logic as the /public endpoint

    Behavior:
      - Retrieves data product by file_id using public access + user project membership logic
      - If COPC has a CRS, enable Cesium and camera sync, and inject the proj4 string + WGS84 center.
      - If no CRS, disable Cesium and show Potree-only with a gentle banner.
    """
    # Determine upload directory
    if os.environ.get("RUNNING_TESTS") == "1":
        upload_dir = settings.TEST_STATIC_DIR
    else:
        upload_dir = settings.STATIC_DIR

    # Get user ID if user is authenticated
    user_id = None
    if current_user:
        user_id = current_user.id

    # Retrieve the data product using the same logic as the public endpoint
    # This checks both public access and user project membership
    data_product = crud.data_product.get_public_data_product_by_id(
        db, file_id=file_id, upload_dir=upload_dir, user_id=user_id
    )

    if not data_product:
        # Return HTML error page instead of JSON for iframe display
        if current_user:
            error_message = (
                "Data product not found or you do not have access to view it"
            )
        else:
            error_message = "Data product not found or not publicly accessible"

        error_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Access Denied</title>
    <style>
      body {{
        margin: 0;
        padding: 0;
        font-family: system-ui, -apple-system, sans-serif;
        background: #f9fafb;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
      }}
      .alert-container {{
        border-left: 4px solid #ef4444;
        background-color: #fef2f2;
        border-radius: 6px;
        padding: 1rem;
        max-width: 400px;
        margin: 1rem;
      }}
      .alert-content {{
        display: flex;
        align-items: center;
        gap: 1rem;
      }}
      .alert-icon {{
        height: 1.5rem;
        width: 1.5rem;
        color: #ef4444;
        flex-shrink: 0;
      }}
      .alert-text {{
        flex: 1;
      }}
      .alert-title {{
        display: block;
        font-weight: 500;
        color: #dc2626;
        margin-bottom: 0.25rem;
      }}
      .alert-message {{
        font-size: 0.875rem;
        color: #b91c1c;
        line-height: 1.5;
      }}
    </style>
  </head>
  <body>
    <div class="alert-container">
      <div class="alert-content">
        <svg class="alert-icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
        <div class="alert-text">
          <strong class="alert-title">Access Denied</strong>
          <div class="alert-message">{error_message}</div>
        </div>
      </div>
    </div>
  </body>
</html>"""
        return HTMLResponse(content=error_html, status_code=404)

    # Extract the COPC path from the data product
    # The URL attribute is dynamically added by set_url_attr in CRUD
    copc_path = getattr(data_product, "url", None)
    if not copc_path:
        error_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Error</title>
    <style>
      body {{
        margin: 0;
        padding: 0;
        font-family: system-ui, -apple-system, sans-serif;
        background: #f9fafb;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
      }}
      .alert-container {{
        border-left: 4px solid #ef4444;
        background-color: #fef2f2;
        border-radius: 6px;
        padding: 1rem;
        max-width: 400px;
        margin: 1rem;
      }}
      .alert-content {{
        display: flex;
        align-items: center;
        gap: 1rem;
      }}
      .alert-icon {{
        height: 1.5rem;
        width: 1.5rem;
        color: #ef4444;
        flex-shrink: 0;
      }}
      .alert-text {{
        flex: 1;
      }}
      .alert-title {{
        display: block;
        font-weight: 500;
        color: #dc2626;
        margin-bottom: 0.25rem;
      }}
      .alert-message {{
        font-size: 0.875rem;
        color: #b91c1c;
        line-height: 1.5;
      }}
    </style>
  </head>
  <body>
    <div class="alert-container">
      <div class="alert-content">
        <svg class="alert-icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
        <div class="alert-text">
          <strong class="alert-title">Error</strong>
          <div class="alert-message">Unable to generate URL for data product</div>
        </div>
      </div>
    </div>
  </body>
</html>"""
        return HTMLResponse(content=error_html, status_code=500)

    # Generate the HTML content using the reusable function
    html_content = generate_potree_viewer_html(copc_path, is_mobile)
    return HTMLResponse(content=html_content)
