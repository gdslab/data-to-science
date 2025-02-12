import axios, { AxiosResponse } from 'axios';
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
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />

      <link href="/potree/libs/potree/potree.css" rel="stylesheet" />
      <link href="/potree/libs/jquery-ui/jquery-ui.min.css" rel="stylesheet" />
      <link href="/potree/libs/openlayers3/ol.css" rel="stylesheet" />
      <link href="/potree/libs/spectrum/spectrum.css" rel="stylesheet" />
      <link href="/potree/libs/jstree/themes/mixed/style.css" rel="stylesheet" />

      <style>	
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
	    </style>

      <base target="_blank">
    </head>
    <body>
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

        viewer.setEDLEnabled(true);
        viewer.setFOV(60);
        viewer.setPointBudget(2_000_000);
        viewer.loadSettingsFromURL();
        viewer.useHQ = true;

        // viewer.setDescription('Loading Entwine-generated EPT format');

        viewer.loadGUI(() => {
          viewer.setLanguage('en');
          $("#menu_tools").next().show();
        });
        
        const path = '${copcUrl.replace(window.origin, '')}';
        const name = 'Potree';

        Potree.loadPointCloud(path, name, function(e) {
          viewer.scene.addPointCloud(e.pointcloud);

          let material = e.pointcloud.material;
          material.size = 1;
          material.shape = Potree.PointShape.CIRCLE;
          material.pointSizeType = Potree.PointSizeType.ADAPTIVE;

          viewer.fitToScreen(0.5);
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
          elToolbar.find('#sldPointBudget').slider({
            value: viewer.getPointBudget(),
            min: 100_000,
            max: 2_000_000,
            step: 100_000,
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
      <iframe className="h-full w-full" srcDoc={initialContent}></iframe>
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </Fragment>
  );
}
