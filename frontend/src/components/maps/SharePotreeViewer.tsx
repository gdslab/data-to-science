import { AxiosResponse } from 'axios';
import { Fragment, useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';

import { DataProduct } from '../pages/projects/Project';
import { AlertBar, Status } from '../Alert';

import api from '../../api';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function SharePotreeViewer() {
  const [copcUrl, setCopcUrl] = useState('');
  const [status, setStatus] = useState<Status | null>(null);

  const query = useQuery();
  const fileID = query.get('file_id');

  // Detect mobile device outside of iframe content
  const isMobile =
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    ) || window.innerWidth < 768;

  useEffect(() => {
    async function fetchCOPC(fileID) {
      try {
        const response: AxiosResponse<DataProduct> = await api.get(
          `/public?file_id=${fileID}`
        );
        if (response.status === 200) {
          setCopcUrl(response.data.url);
        } else {
          setStatus({ type: 'error', msg: 'Unable to load COPC' });
        }
      } catch (_err) {
        setStatus({ type: 'error', msg: 'Unable to load COPC' });
      }
    }

    if (fileID) {
      fetchCOPC(fileID);
    }
  }, []);

  const initialContent = `<!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0" />

      <link href="/potree/libs/potree/potree.css" rel="stylesheet" />
      <link href="/potree/libs/jquery-ui/jquery-ui.min.css" rel="stylesheet" />
      <link href="/potree/libs/openlayers3/ol.css" rel="stylesheet" />
      <link href="/potree/libs/spectrum/spectrum.css" rel="stylesheet" />
      <link href="/potree/libs/jstree/themes/mixed/style.css" rel="stylesheet" />

      <style>	
        body {
          margin: 0;
          padding: 0;
          overflow: hidden;
          /* Mobile touch optimizations */
          touch-action: manipulation;
          user-select: none;
          -webkit-user-select: none;
          -webkit-touch-callout: none;
        }
        
        .potree_container {
          width: 100%;
          height: 100vh;
          min-height: 300px;
          overflow: hidden;
        }
        
        #potree_render_area {
          width: 100%;
          height: 100%;
          min-height: inherit;
        }

        #potree_render_area,
        #potree_render_area canvas {
          touch-action: none;
          outline: none;
          -webkit-user-select: none;
          -moz-user-select: none;
          -ms-user-select: none;
          user-select: none;
          cursor: crosshair;
        }
        
        #potree_toolbar {
          position: absolute; 
          z-index: 10000; 
          left: 100px; 
          top: 0px;
          background: black;
          color: white;
          padding: 0.3em 0.8em;
          font-family: "system-ui";
          border-radius: 0em 0em 0.3em 0.3em;
          display: flex;
          /* Mobile responsive toolbar */
          flex-wrap: wrap;
          max-width: calc(100vw - 120px);
        }

        .potree_toolbar_label {
          text-align: center;
          font-size: smaller;
          opacity: 0.9;
        }

        .potree_toolbar_separator {
          background: white;
          padding: 0px;
          margin: 5px 10px;
          width: 1px;
        }
        
        /* Mobile-specific toolbar adjustments */
        @media (max-width: 768px) {
          #potree_toolbar {
            left: 60px;  /* Increased from 10px to provide space for sidebar menu button */
            top: 10px;
            font-size: 12px;
            padding: 0.2em 0.5em;
            max-width: calc(100vw - 80px);  /* Adjusted for new left position */
          }
          
          .annotation-action-icon {
            width: 1.5em !important;
            height: auto !important;
          }
        }
        
        /* Loading indicator */
        .loading-indicator {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          background: rgba(0,0,0,0.7);
          color: white;
          padding: 10px 20px;
          border-radius: 5px;
          font-size: 14px;
          z-index: 20000;
        }
	    </style>

      <base target="_blank">
    </head>
    <body>
      <div id="loading" class="loading-indicator">${
        isMobile
          ? 'Loading point cloud (mobile mode)...'
          : 'Loading point cloud...'
      }</div>
      
      <script>
        // Mobile device detection (passed from parent)
        const isMobile = ${isMobile};
        
        // WebGL support check
        function checkWebGLSupport() {
          const canvas = document.createElement('canvas');
          const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
          if (!gl) {
            const loadingEl = document.getElementById('loading');
            if (loadingEl) {
              loadingEl.textContent = 'WebGL not supported on this device';
              loadingEl.style.background = 'rgba(255,0,0,0.8)';
            }
            return false;
          }
          return true;
        }
        
        if (!checkWebGLSupport()) {
          console.error('WebGL not supported');
        }
      </script>
      
      <script src='/potree/libs/jquery/jquery-3.1.1.min.js'></script>
      <script src='/potree/libs/spectrum/spectrum.js'></script>
      <script src='/potree/libs/jquery-ui/jquery-ui.min.js'></script>
      <script src='/potree/libs/other/BinaryHeap.js'></script>
      <script src='/potree/libs/tween/tween.min.js'></script>
      <script src='/potree/libs/d3/d3.js'></script>
      <script src='/potree/libs/proj4/proj4.js'></script>
      <script src='/potree/libs/openlayers3/ol.js'></script>
      <script src='/potree/libs/i18next/i18next.js'></script>
      <script src='/potree/libs/jstree/jstree.js'></script>
      <script src='/potree/libs/copc/index.js'></script>
      <script src='/potree/libs/potree/potree.js'></script>
      <script src='/potree/libs/plasio/js/laslaz.js'></script>

      <div class="potree_container">
        <div id="potree_render_area">
          <div id="potree_toolbar"></div>
        </div>
        <div id="potree_sidebar_container"></div>
      </div>

      <script type="module">
        import * as THREE from "/potree/libs/three.js/build/three.module.js";
        
        window.viewer = new Potree.Viewer(document.getElementById("potree_render_area"));

        // Mobile-specific optimizations
        if (isMobile) {
          // Mobile optimizations: reduce quality and performance demands
          viewer.setEDLEnabled(false);        // Disable expensive effects
          viewer.setPointBudget(500_000);     // Much lower point budget
          viewer.useHQ = false;               // Disable high quality mode
          viewer.setFOV(70);                  // Slightly wider FOV for mobile
        } else {
          // Desktop settings (original)
          viewer.setEDLEnabled(true);
          viewer.setPointBudget(2_000_000);
          viewer.useHQ = true;
          viewer.setFOV(60);
        }
        
        viewer.loadSettingsFromURL();
        
        if (isMobile) {
          viewer.setControls(viewer.orbitControls);
        } else {
          viewer.setControls(viewer.earthControls);
        }

        // viewer.setDescription('Loading Entwine-generated EPT format');

        viewer.loadGUI(() => {
          viewer.setLanguage('en');
          $("#menu_tools").next().show();
        });
        
        const path = '${copcUrl.replace(window.origin, '')}';
        const name = 'Potree';

        Potree.loadPointCloud(path, name, function(e) {
          try {
            if (e.type === 'loading_failed') {
              throw new Error('Failed to load point cloud: ' + (e.message || 'Unknown error'));
            }
            
            const pointcloud = e.pointcloud;
            if (!pointcloud) {
              throw new Error('Point cloud object is null');
            }
            
            viewer.scene.addPointCloud(pointcloud);

            let material = pointcloud.material;
            
            // Mobile-specific material settings
            if (isMobile) {
              material.size = 2;  // Larger points for mobile touch
              material.pointSizeType = Potree.PointSizeType.FIXED;
            } else {
              material.size = 1;
              material.pointSizeType = Potree.PointSizeType.ADAPTIVE;
            }
            
            material.shape = Potree.PointShape.CIRCLE;

            viewer.fitToScreen(0.5);
            
            // Remove loading indicator
            const loadingEl = document.getElementById('loading');
            if (loadingEl) {
              loadingEl.remove();
            }
          } catch (error) {
            console.error('Point cloud loading error:', error);
            const loadingEl = document.getElementById('loading');
            if (loadingEl) {
              loadingEl.textContent = 'Error loading point cloud: ' + error.message;
              loadingEl.style.background = 'rgba(255,0,0,0.8)';
            }
          }
        });
      </script>

      <script type="module">
        import * as THREE from "/potree/libs/three.js/build/three.module.js";

        // source: https://github.com/potree/potree/blob/develop/examples/toolbar.html
        
        // HTML
        const elToolbar = $("#potree_toolbar");
        elToolbar.html(\`
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

        \`);

        // CONTENT & ACTIONS
        { // ATTRIBUTE
          elToolbar.find("img[name=action_elevation]").click( () => {
            viewer.scene.pointclouds.forEach( pc => pc.material.activeAttributeName = "elevation" );
          });
      
          elToolbar.find("img[name=action_rgb]").click( () => {
            viewer.scene.pointclouds.forEach( pc => pc.material.activeAttributeName = "rgba" );
          });
        }

        { // GRADIENT
          const schemes = Object.keys(Potree.Gradients).map(name => ({name: name, values: Potree.Gradients[name]}));
          const elGradientSchemes = elToolbar.find("span[name=gradient_schemes]");
      
          for(const scheme of schemes){
            const elButton = $(\`
              <span style=""></span>
            \`);
      
            const svg = Potree.Utils.createSvgGradient(scheme.values);
            svg.setAttributeNS(null, "class", \`button-icon\`);
            svg.style.height = "2em";
            svg.style.width = "1.3em";
      
            elButton.append($(svg));
      
            elButton.click( () => {
              for(const pointcloud of viewer.scene.pointclouds){
                pointcloud.material.activeAttributeName = "elevation";
                pointcloud.material.gradient = Potree.Gradients[scheme.name];
              }
            });
      
            elGradientSchemes.append(elButton);
          }
        }
      
        { // MEASURE
          elToolbar.find("img[name=action_measure_point]").click( () => {
            const measurement = viewer.measuringTool.startInsertion({
              showDistances: false,
              showAngles: false,
              showCoordinates: true,
              showArea: false,
              closed: true,
              maxMarkers: 1,
              name: 'Point'
            });
          });
      
          elToolbar.find("img[name=action_measure_distance]").click( () => {
            const measurement = viewer.measuringTool.startInsertion({
              showDistances: true,
              showArea: false,
              closed: false,
              name: 'Distance'
            });
          });
      
          elToolbar.find("img[name=action_measure_circle]").click( () => {
            const measurement = viewer.measuringTool.startInsertion({
              showDistances: false,
              showHeight: false,
              showArea: false,
              showCircle: true,
              showEdges: false,
              closed: false,
              maxMarkers: 3,
              name: 'Circle'
            });
          });
        }
      
        { // MATERIAL
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
          for(let option of options){
            let elOption = $(\`<option>\${option}</option>\`);
            attributeSelection.append(elOption);
          }
      
          const updateMaterialSelection = (event, ui) => {
            let selectedValue = attributeSelection.selectmenu().val();
      
            for(const pointcloud of viewer.scene.pointclouds){
              pointcloud.material.activeAttributeName = selectedValue;
            }
          };
      
          attributeSelection.selectmenu({change: updateMaterialSelection});
        }
      
        { // POINT BUDGET
          const minBudget = isMobile ? 50_000 : 100_000;
          const maxBudget = isMobile ? 1_000_000 : 2_000_000;
          const stepBudget = isMobile ? 50_000 : 100_000;
          
          elToolbar.find('#sldPointBudget').slider({
            value: viewer.getPointBudget(),
            min: minBudget,
            max: maxBudget,
            step: stepBudget,
            slide: (event, ui) => { viewer.setPointBudget(ui.value); }
          });
      
          const onBudgetChange = () => {
            let budget = (viewer.getPointBudget() / (1000_000)).toFixed(1) + "M";
            elToolbar.find('span[name=lblPointBudget]').html(budget);
          };
      
          onBudgetChange();
          viewer.addEventListener("point_budget_changed", onBudgetChange);
        }
      </script>
    </body>
  </html>`;
  return (
    <Fragment>
      <iframe
        className="h-full w-full touch-none"
        srcDoc={initialContent}
        sandbox="allow-same-origin allow-scripts allow-popups allow-pointer-lock allow-modals allow-forms"
      ></iframe>
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </Fragment>
  );
}
