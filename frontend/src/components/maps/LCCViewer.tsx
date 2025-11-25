import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FirstPersonControls } from './LCCFirstPersonControls';
// @ts-ignore
import { LCCRender } from '../../vendor/lcc-web-sdk/lcc-0.5.4.js';
import LoadingBars from '../LoadingBars';
import LCCControlsOverlay from './LCCControlsOverlay';

declare global {
  interface Window {
    LCCRender?: typeof LCCRender;
    lccObj?: any;
  }
}

export default function LCCViewer({ lccUrl }: { lccUrl: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const initializedRef = useRef(false);
  const droneModelRef = useRef<THREE.Group | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<FirstPersonControls | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const lccObjRef = useRef<any>(null);
  const [progress, setProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [droneVisible, setDroneVisible] = useState(true);
  const [showControls, setShowControls] = useState(false);
  const [quality, setQuality] = useState<
    'very-low' | 'low' | 'medium' | 'high' | 'very-high'
  >('medium');

  useEffect(() => {
    setIsLoading(true);
    setProgress(0);
    const container = containerRef.current;
    if (!container || initializedRef.current) return undefined;
    initializedRef.current = true;

    const scene = new THREE.Scene();
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);
    const sunLight = new THREE.DirectionalLight(0xfff4e0, 0.7);
    sunLight.position.set(0, 50, 0);
    sunLight.castShadow = true;
    scene.add(sunLight);
    const droneFillLight = new THREE.PointLight(0xffffff, 0.15, 20);
    scene.add(droneFillLight);
    scene.fog = new THREE.FogExp2(0xdddddd, 0.0005);

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.setClearColor(0x000000);
    renderer.domElement.tabIndex = 0;
    renderer.domElement.style.outline = 'none';
    container.appendChild(renderer.domElement);

    const camera = new THREE.PerspectiveCamera(60, width / height, 1, 1000);
    camera.position.set(0, 2, 0);
    cameraRef.current = camera;

    // Clock for delta time
    const clock = new THREE.Clock();

    // Drone variables
    const gltfLoader = new GLTFLoader();
    let droneModel: THREE.Group | null = null;
    let droneMixer: THREE.AnimationMixer | null = null;
    const droneForwardOffset = 1.0;
    const droneScale = 1.0;
    const cameraDirection = new THREE.Vector3();

    // Collision variables
    const capsuleHeight = 0.3;
    const capsuleRadius = 0.4;
    const collisionCapsule = {
      start: new THREE.Vector3(),
      end: new THREE.Vector3(),
      radius: capsuleRadius,
      noDelta: false,
    };
    const collisionDelta = new THREE.Vector3();
    let collisionEnabled = false;

    // First person controls
    const firstPersonControl = new FirstPersonControls(
      camera,
      renderer.domElement
    );
    firstPersonControl.enabled = true;
    firstPersonControl.movementSpeed = 5;
    firstPersonControl.lookSpeed = 0.1;
    firstPersonControl.lookAt(new THREE.Vector3(0, 2, 1));
    controlsRef.current = firstPersonControl;

    // Ensure canvas can receive events
    renderer.domElement.focus();

    // Load drone model
    gltfLoader.load(
      `${location.origin}/models/animated_drone.glb`,
      (gltf) => {
        droneModel = gltf.scene;
        droneModel.visible = droneVisible;
        droneModel.scale.set(droneScale, droneScale, droneScale);
        droneModelRef.current = droneModel;
        scene.add(droneModel);

        if (gltf.animations && gltf.animations.length) {
          const hoverClip =
            THREE.AnimationClip.findByName(gltf.animations, 'hover') ||
            gltf.animations[0];
          droneMixer = new THREE.AnimationMixer(droneModel);
          const droneAction = droneMixer.clipAction(hoverClip);
          droneAction.play();
        }
      },
      undefined,
      (error) => {
        console.error('Failed to load drone model', error);
      }
    );

    // Use the model matrix to change the model coordinate system
    const modelMatrix = new THREE.Matrix4(
      -1,
      0,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      0,
      1
    );

    const dataPath = new URL(lccUrl, window.location.origin).href;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const lccObj: any = LCCRender.load(
      {
        camera,
        scene,
        dataPath,
        renderLib: THREE,
        canvas: renderer.domElement,
        renderer,
        useEnv: true,
        useIndexDB: true,
        useLoadingEffect: true,
        modelMatrix,
        appKey: null,
      },
      () => {
        lccObj.setMaxDistance(100);
        lccObj.setMaxSplats(3000000);
        lccObj.setMaxNodeSplats(1500000);
        lccObjRef.current = lccObj;
        window.LCCRender = LCCRender;
        window.lccObj = lccObj;
        const ret = lccObj.hasCollision?.();
        collisionEnabled = !!ret;
        if (ret) {
          console.log('Collision function available');
        } else {
          console.log('Collision function is not available');
        }
        setIsLoading(false);
      },
      (percent: number) => {
        setProgress(percent);
      },
      () => {
        console.error('LCC loading failure');
        setIsLoading(false);
      }
    );

    function resolveCameraCollision() {
      if (!collisionEnabled || !lccObj?.intersectsCapsule) {
        return;
      }
      camera.getWorldDirection(cameraDirection).normalize();
      const capsuleBase = camera.position
        .clone()
        .addScaledVector(cameraDirection, droneForwardOffset);
      collisionCapsule.end.copy(capsuleBase);
      collisionCapsule.start
        .copy(capsuleBase)
        .addScaledVector(camera.up, -capsuleHeight);
      const result = lccObj.intersectsCapsule(collisionCapsule);
      if (result && result.hit && result.delta) {
        const delta = result.delta;
        if (delta.isVector3) {
          collisionDelta.copy(delta);
        } else {
          collisionDelta.set(delta.x || 0, delta.y || 0, delta.z || 0);
        }
        camera.position.add(collisionDelta);
      }
    }

    function updateDrone(deltaTime: number) {
      if (!droneModel) {
        return;
      }
      camera.getWorldDirection(cameraDirection).normalize();
      droneModel.position
        .copy(camera.position)
        .addScaledVector(cameraDirection, droneForwardOffset);
      droneModel.quaternion.copy(camera.quaternion);
      droneFillLight.position.copy(droneModel.position);
      if (droneMixer) {
        droneMixer.update(deltaTime);
      }
    }

    function render() {
      const deltaTime = clock.getDelta();
      if (firstPersonControl?.enabled) {
        firstPersonControl.update(deltaTime);
        resolveCameraCollision();
      }
      updateDrone(deltaTime);
      LCCRender.update();
      renderer.render(scene, camera);
    }

    renderer.setAnimationLoop(render);

    const handleResize = () => {
      // Recompute size when the surrounding layout (LayerPane) changes
      const nextWidth =
        container.clientWidth > 0 ? container.clientWidth : window.innerWidth;
      const nextHeight =
        container.clientHeight > 0
          ? container.clientHeight
          : window.innerHeight;
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, nextHeight);
      firstPersonControl.handleResize();
    };

    window.addEventListener('resize', handleResize);
    if ('ResizeObserver' in window) {
      resizeObserverRef.current = new ResizeObserver(() => handleResize());
      resizeObserverRef.current.observe(container);
    }
    // Re-run resize on next frames to catch layout shifts from collapsing the layer pane
    requestAnimationFrame(() => {
      handleResize();
      requestAnimationFrame(handleResize);
    });

    return () => {
      window.removeEventListener('resize', handleResize);
      resizeObserverRef.current?.disconnect();
      resizeObserverRef.current = null;
    };
  }, [lccUrl]);

  useEffect(() => {
    if (droneModelRef.current) {
      droneModelRef.current.visible = droneVisible;
    }
  }, [droneVisible]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === 'KeyH') {
        setDroneVisible((prev) => !prev);
      } else if (event.code === 'KeyC') {
        setShowControls((prev) => !prev);
      } else if (event.code === 'KeyR') {
        // Reset camera to starting position
        if (cameraRef.current && controlsRef.current) {
          cameraRef.current.position.set(0, 2, 0);
          controlsRef.current.lookAt(new THREE.Vector3(0, 2, 1));
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (!lccObjRef.current) return;

    const qualitySettings = {
      'very-low': {
        maxDistance: 100 / 4,
        maxSplats: 3000000 / 4,
        maxNodeSplats: 1500000 / 4,
      },
      low: {
        maxDistance: 100 / 2,
        maxSplats: 3000000 / 2,
        maxNodeSplats: 1500000 / 2,
      },
      medium: {
        maxDistance: 100,
        maxSplats: 3000000,
        maxNodeSplats: 1500000,
      },
      high: {
        maxDistance: 100 * 2.5,
        maxSplats: 3000000 * 2,
        maxNodeSplats: 1500000 * 2,
      },
      'very-high': {
        maxDistance: 100 * 5,
        maxSplats: 3000000 * 4,
        maxNodeSplats: 1500000 * 4,
      },
    };

    const settings = qualitySettings[quality];
    lccObjRef.current.setMaxDistance(settings.maxDistance);
    lccObjRef.current.setMaxSplats(settings.maxSplats);
    lccObjRef.current.setMaxNodeSplats(settings.maxNodeSplats);
  }, [quality]);

  return (
    <div className="relative h-full w-full overflow-hidden">
      <div ref={containerRef} className="absolute inset-0" />
      <div className="absolute left-3 top-3 z-10 flex flex-col gap-2">
        <div className="flex gap-2">
          <button
            onClick={() => setDroneVisible(!droneVisible)}
            className="cursor-pointer rounded border border-white/30 bg-black/70 px-4 py-2 text-sm font-medium text-white"
          >
            {droneVisible ? 'Hide Drone' : 'Show Drone'}
          </button>
          <button
            onClick={() => setShowControls(!showControls)}
            className="cursor-pointer rounded border border-white/30 bg-black/70 px-4 py-2 text-sm font-medium text-white"
          >
            {showControls ? 'Hide Controls' : 'Show Controls'}
          </button>
        </div>
        <div className="flex items-center gap-2 rounded border border-white/30 bg-black/70 px-3 py-2">
          <span className="text-sm font-medium text-white">Quality:</span>
          <div className="flex overflow-hidden rounded border border-white/30">
            <button
              onClick={() => setQuality('very-low')}
              className={`px-2 py-1 text-xs font-medium transition-colors ${
                quality === 'very-low'
                  ? 'bg-white/30 text-white'
                  : 'bg-black/40 text-white/70 hover:bg-white/10'
              }`}
            >
              Very Low
            </button>
            <button
              onClick={() => setQuality('low')}
              className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
                quality === 'low'
                  ? 'bg-white/30 text-white'
                  : 'bg-black/40 text-white/70 hover:bg-white/10'
              }`}
            >
              Low
            </button>
            <button
              onClick={() => setQuality('medium')}
              className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
                quality === 'medium'
                  ? 'bg-white/30 text-white'
                  : 'bg-black/40 text-white/70 hover:bg-white/10'
              }`}
            >
              Medium
            </button>
            <button
              onClick={() => setQuality('high')}
              className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
                quality === 'high'
                  ? 'bg-white/30 text-white'
                  : 'bg-black/40 text-white/70 hover:bg-white/10'
              }`}
            >
              High
            </button>
            <button
              onClick={() => setQuality('very-high')}
              className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
                quality === 'very-high'
                  ? 'bg-white/30 text-white'
                  : 'bg-black/40 text-white/70 hover:bg-white/10'
              }`}
            >
              Very High
            </button>
          </div>
        </div>
      </div>
      {showControls && <LCCControlsOverlay />}
      {droneVisible && (
        <div className="absolute bottom-3 left-3 z-10 text-xs text-white/60">
          Animated Drone by hartwelkisaka (CC BY 4.0)
        </div>
      )}
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gradient-to-b from-black/55 to-black/35 text-white">
          <LoadingBars />
          <div className="text-sm opacity-90">
            Loading LCC scene... {Math.round(progress * 100)}%
          </div>
        </div>
      )}
    </div>
  );
}
