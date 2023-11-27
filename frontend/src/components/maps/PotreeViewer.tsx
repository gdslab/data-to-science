import Frame from 'react-frame-component';

export default function PotreeViewer({ eptPath }: { eptPath: string }) {
  const initialContent = `<!DOCTYPE html>
  <html>
    <head>
      <link href="/potree/libs/potree/potree.css" rel="stylesheet" />
      <link href="/potree/libs/jquery-ui/jquery-ui.min.css" rel="stylesheet" />
      <link href="/potree/libs/openlayers3/ol.css" rel="stylesheet" />
      <link href="/potree/libs/spectrum/spectrum.css" rel="stylesheet" />
      <link href="/potree/libs/jstree/themes/mixed/style.css" rel="stylesheet" />
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
      <script src='/potree/libs/potree/potree.js'></script>
      <script src='/potree/libs/plasio/js/laslaz.js'></script>

      <div class="potree_container">
        <div
          id="potree_render_area"
          style="background-image: url('/potree/resources/images/background.jpg'); left: 300px;"
        ></div>
        <div id="potree_sidebar_container"></div>
      </div>

      <script type="module">
        import * as THREE from "http://localhost/potree/libs/three.js/build/three.module.js";
        window.viewer = new Potree.Viewer(document.getElementById("potree_render_area"));

        viewer.setEDLEnabled(true);
        viewer.setFOV(60);
        viewer.setPointBudget(2_000_000);
        viewer.loadSettingsFromURL();
        viewer.useHQ = true;

        viewer.setDescription('Loading Entwine-generated EPT format');

        viewer.loadGUI(() => {
          viewer.setLanguage('en');
          $('#menu_apperance').next().show();
          viewer.toggleSidebar();
        });
        
        const path = '${eptPath}';
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
    </body>
  </html>`;
  return (
    <Frame initialContent={initialContent} style={{ height: '100vh', width: '100vw' }}>
      <></>
    </Frame>
  );
}
