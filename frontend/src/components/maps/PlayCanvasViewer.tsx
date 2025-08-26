import { RESOLUTION_AUTO, Entity as PcEntity } from 'playcanvas';
import { useEffect, useRef, useState } from 'react';
import { Application, Entity } from '@playcanvas/react';
import { Camera, GSplat } from '@playcanvas/react/components';
import { OrbitControls } from '@playcanvas/react/scripts';
import { useSplat } from '@playcanvas/react/hooks';

function Scene({ splatUrl }: { splatUrl: string }) {
  const { asset } = useSplat(splatUrl);
  const gsplatEntityRef = useRef<PcEntity | null>(null);

  const [controls, setControls] = useState<{
    distanceMin: number;
    distanceMax: number;
    distance: number;
    mouse: { distanceSensitivity: number };
    touch: { distanceSensitivity: number };
    focusEntity: PcEntity | null;
    frameOnStart: boolean;
  }>({
    distanceMin: 0.05,
    distanceMax: 10,
    distance: 3,
    mouse: { distanceSensitivity: 0.1 },
    touch: { distanceSensitivity: 0.1 },
    focusEntity: null,
    frameOnStart: true,
  });

  useEffect(() => {
    if (!asset) return;

    const entity = gsplatEntityRef.current as unknown as {
      gsplat?: {
        instance?: {
          resource?: {
            aabb?: { halfExtents: { x: number; y: number; z: number } };
          };
        };
      };
    } | null;

    // Prefer aabb from asset.resource if available, otherwise fall back to entity.gsplat.instance.resource
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const aabb: any =
      (asset as any)?.resource?.aabb ??
      entity?.gsplat?.instance?.resource?.aabb;
    if (!aabb?.halfExtents) return;

    const hx = aabb.halfExtents.x ?? 1;
    const hy = aabb.halfExtents.y ?? 1;
    const hz = aabb.halfExtents.z ?? 1;
    const radius = Math.max(Math.hypot(hx, hy, hz), 1e-3);

    const distanceMin = Math.max(radius * 0.05, 0.02);
    const distanceMax = Math.max(radius * 30, distanceMin + radius * 2);
    const distance = Math.min(
      Math.max(radius * 3, distanceMin + radius * 0.5),
      distanceMax - radius * 0.1
    );
    const sensitivity = Math.min(Math.max(radius * 0.1, 0.02), 5);

    setControls({
      distanceMin,
      distanceMax,
      distance,
      mouse: { distanceSensitivity: sensitivity },
      touch: { distanceSensitivity: sensitivity },
      focusEntity: (gsplatEntityRef.current as PcEntity | null) ?? null,
      frameOnStart: true,
    });
  }, [asset]);

  if (!asset) return null;

  return (
    <>
      <Entity
        ref={gsplatEntityRef}
        position={[0, -0.7, 0]}
        rotation={[0, 0, 180]}
      >
        <GSplat asset={asset} />
      </Entity>
      <Entity position={[0, 0, -2.5]}>
        <Camera />
        <OrbitControls
          distanceMin={controls.distanceMin}
          distanceMax={controls.distanceMax}
          distance={controls.distance}
          mouse={{ distanceSensitivity: controls.mouse.distanceSensitivity }}
          touch={{ distanceSensitivity: controls.touch.distanceSensitivity }}
          focusEntity={controls.focusEntity}
          frameOnStart={controls.frameOnStart}
        />
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
