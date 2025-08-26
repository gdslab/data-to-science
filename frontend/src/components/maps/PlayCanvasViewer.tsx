import { RESOLUTION_AUTO } from 'playcanvas';
import { Application, Entity } from '@playcanvas/react';
import { Camera, GSplat } from '@playcanvas/react/components';
import { OrbitControls } from '@playcanvas/react/scripts';
import { useSplat } from '@playcanvas/react/hooks';

function Scene({ splatUrl }: { splatUrl: string }) {
  const { asset } = useSplat(splatUrl);

  if (!asset) return null;

  return (
    <>
      <Entity position={[0, -0.7, 0]} rotation={[0, 0, 180]}>
        <GSplat asset={asset} />
      </Entity>
      <Entity position={[0, 0, -2.5]}>
        <Camera />
        <OrbitControls />
      </Entity>
    </>
  );
}

export default function PlayCanvasViewer({ splatUrl }: { splatUrl: string }) {
  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Application
        resolutionMode={RESOLUTION_AUTO}
        graphicsDeviceOptions={{ antialias: false }}
      >
        <Scene splatUrl={splatUrl} />
      </Application>
    </div>
  );
}
