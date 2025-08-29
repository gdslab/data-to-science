import {
  RESOLUTION_AUTO,
  DEVICETYPE_WEBGPU,
  DEVICETYPE_WEBGL2,
  Entity as PcEntity,
} from 'playcanvas';
import { useEffect, useRef, useState } from 'react';
import { Application, Entity } from '@playcanvas/react';
import { Camera, GSplat } from '@playcanvas/react/components';
import { OrbitControls } from '@playcanvas/react/scripts';
import { useApp, useSplat } from '@playcanvas/react/hooks';
import LoadingBars from '../LoadingBars';

function Scene({
  splatUrl,
  onProgress,
  onLoaded,
}: {
  splatUrl: string;
  onProgress: (p: number) => void;
  onLoaded: () => void;
}) {
  const { asset, loading, subscribe } = useSplat(splatUrl);
  const gsplatEntityRef = useRef<PcEntity | null>(null);

  const [controls, setControls] = useState<{
    distanceMin: number;
    distanceMax: number;
    distance: number;
    focusEntity: PcEntity | null;
    frameOnStart: boolean;
  }>({
    distanceMin: 0.05,
    distanceMax: 10,
    distance: 3,
    focusEntity: null,
    frameOnStart: true,
  });

  // subscribe to loading progress
  useEffect(() => {
    const unsubscribe = subscribe?.((meta) => {
      const progress = Math.max(0, Math.min(1, Number(meta?.progress ?? 0)));
      onProgress(progress);
    });
    return () => {
      if (typeof unsubscribe === 'function') unsubscribe();
    };
  }, [subscribe, onProgress]);

  useEffect(() => {
    if (!loading && asset) onLoaded();
  }, [loading, asset, onLoaded]);

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

    setControls({
      distanceMin,
      distanceMax,
      distance,
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
        <GSplat asset={asset} highQualitySH={false} />
      </Entity>
      <Entity position={[0, 0, -2.5]}>
        <Camera />
        <OrbitControls
          distanceMin={controls.distanceMin}
          distanceMax={controls.distanceMax}
          distance={controls.distance}
          focusEntity={controls.focusEntity}
          frameOnStart={controls.frameOnStart}
        />
      </Entity>
    </>
  );
}

export default function PlayCanvasViewer({ splatUrl }: { splatUrl: string }) {
  const [progress, setProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Application
        resolutionMode={RESOLUTION_AUTO}
        deviceTypes={[DEVICETYPE_WEBGPU, DEVICETYPE_WEBGL2]}
        graphicsDeviceOptions={{
          antialias: false,
          powerPreference: 'high-performance',
        }}
      >
        <DeviceTweaks maxPixelRatio={1.5} />
        <Scene
          splatUrl={splatUrl}
          onProgress={(p) => setProgress(p)}
          onLoaded={() => setIsLoading(false)}
        />
      </Application>
      {isLoading && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background:
              'linear-gradient(180deg, rgba(0,0,0,0.55), rgba(0,0,0,0.35))',
            color: 'white',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          <LoadingBars />
          <div style={{ fontSize: 14, opacity: 0.9 }}>
            Loading splat… {Math.round(progress * 100)}%
          </div>
        </div>
      )}
    </div>
  );
}

function DeviceTweaks({ maxPixelRatio = 1.5 }: { maxPixelRatio?: number }) {
  const app = useApp();
  useEffect(() => {
    if (!app) return;
    // cap pixel ratio to reduce fill rate cost on large canvases
    const gd: unknown = (app as unknown as { graphicsDevice?: unknown })
      .graphicsDevice;
    if (
      gd &&
      typeof (gd as { maxPixelRatio?: number }).maxPixelRatio === 'number'
    ) {
      (gd as { maxPixelRatio: number }).maxPixelRatio = maxPixelRatio;
    }
  }, [app, maxPixelRatio]);
  return null;
}
