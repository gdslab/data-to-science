import {
  Controls,
  MathUtils,
  Spherical,
  Vector3,
  Camera,
  PerspectiveCamera,
} from 'three';

const _lookDirection = new Vector3();
const _spherical = new Spherical();
const _target = new Vector3();
const _targetPosition = new Vector3();

class FirstPersonControls extends Controls<Record<string, never>> {
  // Inherited from Controls but need explicit declaration
  enabled: boolean = false;
  object: Camera;
  domElement: HTMLElement | Document | null;

  movementSpeed: number = 1.0;
  lookSpeed: number = 0.005;
  lookVertical: boolean = true;
  autoForward: boolean = false;
  activeLook: boolean = true;
  heightSpeed: boolean = false;
  heightCoef: number = 1.0;
  heightMin: number = 0.0;
  heightMax: number = 1.0;
  constrainVertical: boolean = false;
  verticalMin: number = 0;
  verticalMax: number = Math.PI;
  mouseDragOn: boolean = false;

  private _autoSpeedFactor: number = 0.0;
  private _pointerX: number = 0;
  private _pointerY: number = 0;
  private _moveForward: boolean = false;
  private _moveBackward: boolean = false;
  private _moveLeft: boolean = false;
  private _moveRight: boolean = false;
  private _moveUp: boolean = false;
  private _moveDown: boolean = false;
  private _viewHalfX: number = 0;
  private _viewHalfY: number = 0;
  private _lat: number = 0;
  private _lon: number = 0;
  private _leftButtonPressed: boolean = false;
  private _shiftPressed: boolean = false;

  private _onPointerMove: EventListener;
  private _onPointerDown: EventListener;
  private _onPointerUp: EventListener;
  private _onContextMenu: EventListener;
  private _onKeyDown: EventListener;
  private _onKeyUp: EventListener;
  private _onWheel: EventListener;

  constructor(object: Camera, domElement: HTMLElement | null = null) {
    super(object, domElement);

    this.object = object;
    this.domElement = domElement;
    this.enabled = true;

    this._onPointerMove = this.onPointerMove.bind(this);
    this._onPointerDown = this.onPointerDown.bind(this);
    this._onPointerUp = this.onPointerUp.bind(this);
    this._onContextMenu = this.onContextMenu.bind(this);
    this._onKeyDown = this.onKeyDown.bind(this);
    this._onKeyUp = this.onKeyUp.bind(this);
    this._onWheel = this.onWheel.bind(this);

    if (domElement !== null) {
      this.connect(domElement);
      this.handleResize();
    }

    this._setOrientation();
  }

  connect(element: HTMLElement) {
    super.connect(element);

    window.addEventListener('keydown', this._onKeyDown);
    window.addEventListener('keyup', this._onKeyUp);

    this.domElement?.addEventListener('pointermove', this._onPointerMove);
    this.domElement?.addEventListener('pointerdown', this._onPointerDown);
    this.domElement?.addEventListener('pointerup', this._onPointerUp);
    this.domElement?.addEventListener('contextmenu', this._onContextMenu);
    this.domElement?.addEventListener('wheel', this._onWheel, {
      passive: false,
    } as AddEventListenerOptions);
  }

  disconnect() {
    window.removeEventListener('keydown', this._onKeyDown);
    window.removeEventListener('keyup', this._onKeyUp);

    this.domElement?.removeEventListener('pointermove', this._onPointerMove);
    this.domElement?.removeEventListener('pointerdown', this._onPointerDown);
    this.domElement?.removeEventListener('pointerup', this._onPointerUp);
    this.domElement?.removeEventListener('contextmenu', this._onContextMenu);
    this.domElement?.removeEventListener('wheel', this._onWheel);
  }

  dispose() {
    this.disconnect();
  }

  handleResize() {
    if (this.domElement === document) {
      this._viewHalfX = window.innerWidth / 2;
      this._viewHalfY = window.innerHeight / 2;
    } else if (this.domElement) {
      this._viewHalfX = (this.domElement as HTMLElement).offsetWidth / 2;
      this._viewHalfY = (this.domElement as HTMLElement).offsetHeight / 2;
    }
  }

  lookAt(x: number | Vector3, y?: number, z?: number): this {
    if (x instanceof Vector3) {
      _target.copy(x);
    } else {
      _target.set(x, y!, z!);
    }

    this.object.lookAt(_target);
    this._setOrientation();

    return this;
  }

  update(delta: number) {
    if (this.enabled === false) return;

    if (this.heightSpeed) {
      const y = MathUtils.clamp(
        this.object.position.y,
        this.heightMin,
        this.heightMax
      );
      const heightDelta = y - this.heightMin;
      this._autoSpeedFactor = delta * (heightDelta * this.heightCoef);
    } else {
      this._autoSpeedFactor = 0.0;
    }

    const speedMultiplier = this._shiftPressed ? 1.5 : 0.5;
    const actualMoveSpeed = delta * this.movementSpeed * speedMultiplier;

    if (this._moveForward || (this.autoForward && !this._moveBackward))
      this.object.translateZ(-(actualMoveSpeed + this._autoSpeedFactor));
    if (this._moveBackward) this.object.translateZ(actualMoveSpeed);

    if (this._moveLeft) this.object.translateX(-actualMoveSpeed);
    if (this._moveRight) this.object.translateX(actualMoveSpeed);

    if (this._moveUp) this.object.translateY(actualMoveSpeed);
    if (this._moveDown) this.object.translateY(-actualMoveSpeed);

    let actualLookSpeed = delta * this.lookSpeed;

    if (!this.activeLook || !this._leftButtonPressed) {
      actualLookSpeed = 0;
    }

    let verticalLookRatio = 1;

    if (this.constrainVertical) {
      verticalLookRatio = Math.PI / (this.verticalMax - this.verticalMin);
    }

    this._lon -= this._pointerX * actualLookSpeed;
    if (this.lookVertical)
      this._lat -= this._pointerY * actualLookSpeed * verticalLookRatio;

    this._lat = Math.max(-85, Math.min(85, this._lat));

    let phi = MathUtils.degToRad(90 - this._lat);
    const theta = MathUtils.degToRad(this._lon);

    if (this.constrainVertical) {
      phi = MathUtils.mapLinear(
        phi,
        0,
        Math.PI,
        this.verticalMin,
        this.verticalMax
      );
    }

    const position = this.object.position;

    _targetPosition.setFromSphericalCoords(1, phi, theta).add(position);

    this.object.lookAt(_targetPosition);
  }

  private _setOrientation() {
    const quaternion = this.object.quaternion;

    _lookDirection.set(0, 0, -1).applyQuaternion(quaternion);
    _spherical.setFromVector3(_lookDirection);

    this._lat = 90 - MathUtils.radToDeg(_spherical.phi);
    this._lon = MathUtils.radToDeg(_spherical.theta);
  }

  private onPointerDown(evt: Event) {
    const event = evt as PointerEvent;
    if (this.domElement && this.domElement !== document) {
      (this.domElement as HTMLElement).focus();
    }

    if (this.activeLook && event.button === 0) {
      this._leftButtonPressed = true;
    }

    this.mouseDragOn = true;
  }

  private onPointerUp(evt: Event) {
    const event = evt as PointerEvent;
    if (this.activeLook && event.button === 0) {
      this._leftButtonPressed = false;
    }

    this.mouseDragOn = false;
  }

  private onPointerMove(evt: Event) {
    const event = evt as PointerEvent;
    if (this.domElement === document) {
      this._pointerX = event.pageX - this._viewHalfX;
      this._pointerY = event.pageY - this._viewHalfY;
    } else if (this.domElement) {
      const el = this.domElement as HTMLElement;
      this._pointerX = event.pageX - el.offsetLeft - this._viewHalfX;
      this._pointerY = event.pageY - el.offsetTop - this._viewHalfY;
    }
  }

  private onKeyDown(evt: Event) {
    const event = evt as KeyboardEvent;
    switch (event.code) {
      case 'ArrowUp':
      case 'KeyW':
        this._moveForward = true;
        break;

      case 'ArrowLeft':
      case 'KeyA':
        this._moveLeft = true;
        break;

      case 'ArrowDown':
      case 'KeyS':
        this._moveBackward = true;
        break;

      case 'ArrowRight':
      case 'KeyD':
        this._moveRight = true;
        break;

      case 'Space':
        this._moveUp = true;
        break;
      case 'KeyF':
      case 'ControlLeft':
        this._moveDown = true;
        break;
      case 'ShiftLeft':
      case 'ShiftRight':
        this._shiftPressed = true;
        break;
    }
  }

  private onKeyUp(evt: Event) {
    const event = evt as KeyboardEvent;
    switch (event.code) {
      case 'ArrowUp':
      case 'KeyW':
        this._moveForward = false;
        break;

      case 'ArrowLeft':
      case 'KeyA':
        this._moveLeft = false;
        break;

      case 'ArrowDown':
      case 'KeyS':
        this._moveBackward = false;
        break;

      case 'ArrowRight':
      case 'KeyD':
        this._moveRight = false;
        break;

      case 'Space':
        this._moveUp = false;
        break;
      case 'KeyF':
      case 'ControlLeft':
        this._moveDown = false;
        break;
      case 'ShiftLeft':
      case 'ShiftRight':
        this._shiftPressed = false;
        break;
    }
  }

  private onContextMenu(event: Event) {
    if (this.enabled === false) return;
    event.preventDefault();
  }

  private onWheel(evt: Event) {
    if (this.enabled === false) return;
    const event = evt as WheelEvent;
    event.preventDefault();

    // Cast to PerspectiveCamera to access fov property
    if (!('isPerspectiveCamera' in this.object && this.object.isPerspectiveCamera))
      return;

    const camera = this.object as PerspectiveCamera;
    const zoomSpeed = 0.05;
    const delta = event.deltaY * zoomSpeed;
    const minFov = 30; // Zoomed in (narrow field of view)
    const maxFov = 90; // Zoomed out (wide field of view)

    camera.fov = Math.max(minFov, Math.min(maxFov, camera.fov + delta));
    camera.updateProjectionMatrix();
  }
}

export { FirstPersonControls };
