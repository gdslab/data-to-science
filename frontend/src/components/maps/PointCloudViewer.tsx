import '../../styles/potree/potree.css';
import '../../styles/potree/jquery-ui.min.css';
import '../../styles/potree/ol.css';
import '../../styles/potree/spectrum.css';
import '../../styles/potree/style.min.css';

import { useEffect, useRef } from 'react';

declare var Potree: any;
declare var $: any;

export default function PointCloudViewer({ eptPath }: { eptPath: string }) {
  const potreeRenderAreaRef = useRef(null);

  useEffect(() => {
    if (potreeRenderAreaRef.current) {
      const viewer = new Potree.Viewer(potreeRenderAreaRef.current);

      viewer.setEDLEnabled(true);
      viewer.setFOV(60);
      viewer.setPointBudget(2_000_000);
      viewer.loadSettingsFromURL();

      viewer.setDescription('Loading Entwine-generated EPT format');

      viewer.loadGUI(() => {
        viewer.setLanguage('en');
        $('#menu_apperance').next().show();
      });

      const path = eptPath;
      const name = 'ept';

      Potree.loadPointCloud(path, name, function (e: any) {
        viewer.scene.addPointCloud(e.pointcloud);

        let material = e.pointcloud.material;
        material.size = 1;
        material.pointSizeType = Potree.PointSizeType.ADAPTIVE;

        viewer.fitToScreen(0.5);
      });
    }
  }, [potreeRenderAreaRef.current]);

  useEffect(
    () => () => {
      potreeRenderAreaRef.current = null;
    },
    []
  );

  return (
    <div
      className="potree_container"
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        left: '48px',
      }}
    >
      <div
        ref={potreeRenderAreaRef}
        id="potree_render_area"
        style={{
          backgroundImage: `url('/potree/resources/images/background.jpg')`,
          left: '300px',
        }}
      ></div>
      <div id="potree_sidebar_container"></div>
    </div>
  );
}
