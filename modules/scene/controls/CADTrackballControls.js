
/**
 * Added support of orthographic camera to original implementation
 * 
 * @author Eberhard Graether / http://egraether.com/
 * @author Mark Lundin 	/ http://mark-lundin.com
 * @author Simone Manini / http://daron1337.github.io
 * @author Luca Antiga 	/ http://lantiga.github.io
 */

 import DPR from 'dpr';

export function CADTrackballControls( object, domElement ) {

  const _this = this;
  const STATE = { NONE: - 1, ROTATE: 0, ZOOM: 1, PAN: 2, TOUCH_ROTATE: 3, TOUCH_ZOOM_PAN: 4 };

  this.object = object;
  this.domElement = ( domElement !== undefined ) ? domElement : document;

  // API

  this.enabled = true;

  this.screen = { left: 0, top: 0, width: 0, height: 0 };

  this.rotateSpeed = 1.0;
  this.zoomSpeed = 1.2;
  this.panSpeed = 0.3;

  this.noRotate = false;
  this.noZoom = false;
  this.noPan = false;

  this.staticMoving = false;
  this.dynamicDampingFactor = 0.2;

  this.minDistance = 0;
  this.maxDistance = Infinity;

  this.keys = [ 65 /*A*/, 83 /*S*/, 68 /*D*/ ];

  // internals

  this.target = new THREE.Vector3();

  this.projectionChanged = false;
  this.projectionZoomSpeed = 0.5;

  const EPS = 0.000001;

  const lastPosition = new THREE.Vector3();

  let _state = STATE.NONE,
    _prevState = STATE.NONE,
    _lastAngle = 0,
    _touchZoomDistanceStart = 0,
    _touchZoomDistanceEnd = 0;

  const _eye = new THREE.Vector3(),

    _movePrev = new THREE.Vector2(),
    _moveCurr = new THREE.Vector2(),

    _lastAxis = new THREE.Vector3(),

    _zoomStart = new THREE.Vector2(),
    _zoomEnd = new THREE.Vector2(),

    _panStart = new THREE.Vector2(),
    _panEnd = new THREE.Vector2();

  // for reset

  this.target0 = this.target.clone();
  this.position0 = this.object.position.clone();
  this.up0 = this.object.up.clone();

  this.movePrev = _movePrev;
  this.moveCurr = _moveCurr;
  // events

  const startEvent = { type: 'start' };
  const endEvent = { type: 'end' };


  // methods

  //Setters for internals
   this.setState = function(state) {
    if (state == -1){
      _state = STATE.NONE;
    } else if (state == 0){
      _state = STATE.ROTATE;
    } else if (state == 1){
      _state = STATE.ZOOM;
    } else if (state == 2){
      _state = STATE.PAN;
    } else if (state == 3){
      _state = STATE.TOUCH_ROTATE;
    } else if (state == 4){
      _state = STATE.TOUCH_ZOOM_PAN;
    }
  };

   this.setMovePrev = function(x, y) {
    _movePrev.set(x, y);
  };

  this.setMoveCurr = function(x, y) {
    _moveCurr.set(x, y);
  };

  this.setLastAxis = function(x, y, z) {
    _lastAxis.set(x, y, z);
  };

  this.setZoomStart = function(x, y) {
    _zoomStart.set(x, y);
  };

  this.setZoomEnd = function(x, y) {
    _zoomEnd.set(x, y);
  };

  this.setPanStart = function(x, y) {
    _panStart.set(x, y);
  };

  this.setPanEnd = function(x, y) {
    _panEnd.set(x, y);
  };

  this.handleResize = function () {
    if (this.domElement === document) {
      this.screen.left = 0;
      this.screen.top = 0;
      this.screen.width = window.innerWidth;
      this.screen.height = window.innerHeight;
    } else {
      const box = this.domElement.getBoundingClientRect();
      const d = this.domElement.ownerDocument.documentElement;
      this.screen.left = box.left + window.pageXOffset - d.clientLeft;
      this.screen.top = box.top + window.pageYOffset - d.clientTop;
      this.screen.width = box.width;
      this.screen.height = box.height;
    }
  };

  this.handleEvent = function (event) {
    if (typeof this[event.type] == 'function') {
      this[event.type](event);
    }
  };

  const getMouseOnScreen = (function () {
    const vector = new THREE.Vector2();
    return function getMouseOnScreen(pageX, pageY) {
      vector.set(
        (pageX - _this.screen.left) / _this.screen.width,
        (pageY - _this.screen.top) / _this.screen.height
      );
      return vector;
    };
  }());

  const getMouseOnCircle = (function () {
    const vector = new THREE.Vector2();
    return function getMouseOnCircle(pageX, pageY) {
      vector.set(
        ((pageX - _this.screen.width * 0.5 - _this.screen.left) / (_this.screen.width * 0.5)),
        ((_this.screen.height + 2 * (_this.screen.top - pageY)) / _this.screen.width)
      );
      return vector;
    };
  }());

  this.rotateCamera = (function () {
    const axis = new THREE.Vector3(),
      quaternion = new THREE.Quaternion(),
      eyeDirection = new THREE.Vector3(),
      objectUpDirection = new THREE.Vector3(),
      objectSidewaysDirection = new THREE.Vector3(),
      moveDirection = new THREE.Vector3();

    let angle;

    // console.log('Rotating Camera by', _moveCurr, _movePrev)

    return function rotateCamera() {
      // console.log('Rotating Camera by', _moveCurr, _movePrev); // Move log inside the function
      moveDirection.set(_moveCurr.x - _movePrev.x, _moveCurr.y - _movePrev.y, 0);
      angle = moveDirection.length();

      // console.log('Rotating Camera by Angle', angle)

      if (angle) {
        console.log('Rotating Camera by Angle', angle)
        _eye.copy(_this.object.position).sub(_this.target);

        eyeDirection.copy(_eye).normalize();
        objectUpDirection.copy(_this.object.up).normalize();
        objectSidewaysDirection.crossVectors(objectUpDirection, eyeDirection).normalize();

        objectUpDirection.setLength(_moveCurr.y - _movePrev.y);
        objectSidewaysDirection.setLength(_moveCurr.x - _movePrev.x);

        moveDirection.copy(objectUpDirection.add(objectSidewaysDirection));

        axis.crossVectors(moveDirection, _eye).normalize();

        angle *= _this.rotateSpeed;
        quaternion.setFromAxisAngle(axis, angle);

        _eye.applyQuaternion(quaternion);
        _this.object.up.applyQuaternion(quaternion);

        _lastAxis.copy(axis);
        _lastAngle = angle;
      } else if (!_this.staticMoving && _lastAngle) {
        _lastAngle *= Math.sqrt(1.0 - _this.dynamicDampingFactor);
        _eye.copy(_this.object.position).sub(_this.target);
        quaternion.setFromAxisAngle(_lastAxis, _lastAngle);
        _eye.applyQuaternion(quaternion);
        _this.object.up.applyQuaternion(quaternion);
      }

      _movePrev.copy(_moveCurr);
    };
  }());

  this.setCameraMode = function (isOrthographic) {
    this.noZoom = isOrthographic;
    this.projectionZoom = isOrthographic;
  };

  this.zoomCamera = function () {
    let factor;

    if (_state === STATE.TOUCH_ZOOM_PAN) {
      factor = _touchZoomDistanceStart / _touchZoomDistanceEnd;
      _touchZoomDistanceStart = _touchZoomDistanceEnd;
      _eye.multiplyScalar(factor);
    } else {
      factor = 1.0 + (_zoomEnd.y - _zoomStart.y) * _this.zoomSpeed;
      if (factor !== 1.0 && factor > 0.0) {
        _eye.multiplyScalar(factor);
      }
      if (_this.staticMoving) {
        _zoomStart.copy(_zoomEnd);
      } else {
        _zoomStart.y += (_zoomEnd.y - _zoomStart.y) * this.dynamicDampingFactor;
      }
    }
  };

  this.panCamera = (function () {
    const mouseChange = new THREE.Vector2(),
      objectUp = new THREE.Vector3(),
      pan = new THREE.Vector3();

      console.log('Panning Camera by', _panEnd, _panStart);
    return function panCamera() {
      mouseChange.copy(_panEnd).sub(_panStart);
 
      if (mouseChange.lengthSq()) {
        mouseChange.multiplyScalar(_eye.length() * _this.panSpeed);
        pan.copy(_eye).cross(_this.object.up).setLength(mouseChange.x);
        pan.add(objectUp.copy(_this.object.up).setLength(mouseChange.y));
        _this.object.position.add(pan);
        _this.target.add(pan);
        if (_this.staticMoving) {
          _panStart.copy(_panEnd);
        } else {
          _panStart.add(mouseChange.subVectors(_panEnd, _panStart).multiplyScalar(_this.dynamicDampingFactor));
        }
      }
    };
  }());

  this.checkDistances = function () {
    if (!_this.noZoom || !_this.noPan) {
      if (_eye.lengthSq() > _this.maxDistance * _this.maxDistance) {
        _this.object.position.addVectors(_this.target, _eye.setLength(_this.maxDistance));
        _zoomStart.copy(_zoomEnd);
      }
      if (_eye.lengthSq() < _this.minDistance * _this.minDistance) {
        _this.object.position.addVectors(_this.target, _eye.setLength(_this.minDistance));
        _zoomStart.copy(_zoomEnd);
      }
    }
  };

  this.evaluate = function () {
    this.panSpeed = DPR / this.object.zoom;

    _eye.subVectors(_this.object.position, _this.target);

    if (!_this.noRotate) {
      _this.rotateCamera();
    }

    if (!_this.noZoom) {
      _this.zoomCamera();
    }

    if (!_this.noPan) {
      _this.panCamera();
    }

    _this.object.position.addVectors(_this.target, _eye);

    _this.checkDistances();

    _this.object.lookAt(_this.target);

    const needsRender = lastPosition.distanceToSquared(_this.object.position) > EPS || this.projectionChanged;
    if (needsRender) {
      this.projectionChanged = false;
      lastPosition.copy(_this.object.position);
    }
    return needsRender;
  };

  this.reset = function () {
    _state = STATE.NONE;
    _prevState = STATE.NONE;

    _this.target.copy(_this.target0);
    _this.object.position.copy(_this.position0);
    _this.object.up.copy(_this.up0);

    _eye.subVectors(_this.object.position, _this.target);

    _this.object.lookAt(_this.target);

    lastPosition.copy(_this.object.position);
  };

  // listeners
  function keydown(event) {
    if (_this.enabled === false) return;

    window.removeEventListener('keydown', keydown);

    _prevState = _state;

    if (_state !== STATE.NONE) {
      return;
    } else if (event.keyCode === _this.keys[STATE.ROTATE] && !_this.noRotate) {
      _state = STATE.ROTATE;
    } else if (event.keyCode === _this.keys[STATE.ZOOM] && !_this.noZoom) {
      _state = STATE.ZOOM;
    } else if (event.keyCode === _this.keys[STATE.PAN] && !_this.noPan) {
      _state = STATE.PAN;
    }
  }

  function keyup(event) {
    if (_this.enabled === false) return;

    _state = _prevState;

    window.addEventListener('keydown', keydown, false);
  }

  this.simulateMouseMove = function(pageX, pageY) {
    // _state = STATE.ROTATE;
    mousemove({
      type: 'mousemove',
      pageX: pageX,
      pageY: pageY,
      preventDefault: function() {},
      stopPropagation: function() {}
    });
  };


  function mousedown(event) {
    if (_this.enabled === false) return;

    event.preventDefault();
    //event.stopPropagation(); - interfere with entire application

    if (_state === STATE.NONE) {
      _state = event.button;
    }

    if (_state === STATE.ROTATE && !_this.noRotate) {
      _moveCurr.copy(getMouseOnCircle(event.pageX, event.pageY));
      _movePrev.copy(_moveCurr);
    } else if (_state === STATE.ZOOM && !_this.noZoom) {
      _zoomStart.copy(getMouseOnScreen(event.pageX, event.pageY));
      _zoomEnd.copy(_zoomStart);
    } else if (_state === STATE.PAN && !_this.noPan) {
      _panStart.copy(getMouseOnScreen(event.pageX, event.pageY));
      _panEnd.copy(_panStart);
    }

    document.addEventListener('mousemove', mousemove, false);
    document.addEventListener('mouseup', mouseup, false);

    _this.dispatchEvent(startEvent);
  }

  function mousemove(event) {
    console.log('Mouse move event', event.pageX, event.pageY)

    if (_this.enabled === false) return;

    event.preventDefault();
    event.stopPropagation();

    if (_state === STATE.ROTATE && !_this.noRotate) {
      console.log("Rotating Camera by", _moveCurr, _movePrev)
      _movePrev.copy(_moveCurr);
      _moveCurr.copy(getMouseOnCircle(event.pageX, event.pageY));
    } else if (_state === STATE.ZOOM && !_this.noZoom) {
      console.log("Zooming Camera by", _zoomEnd, _zoomStart)
      _zoomEnd.copy(getMouseOnScreen(event.pageX, event.pageY));
    } else if (_state === STATE.PAN && !_this.noPan) {
      console.log("Panning Camera by", _panEnd, _panStart)
      _panEnd.copy(getMouseOnScreen(event.pageX, event.pageY));
    }
  }

  function mouseup(event) {
    if (_this.enabled === false) return;

    event.preventDefault();
    event.stopPropagation();

    _state = STATE.NONE;

    document.removeEventListener('mousemove', mousemove);
    document.removeEventListener('mouseup', mouseup);
    _this.dispatchEvent(endEvent);
  }

  function mousewheel(event) {
    if (_this.enabled === false) return;

    event.preventDefault();
    event.stopPropagation();
    console.log(event.deltaMode, event.deltaY)
    _this.zoomStep(event.deltaMode, event.deltaY);
  }

  this.zoomStep = function (deltaMode, delta) {
    if (_this.projectionZoom) {
      let speed = _this.projectionZoomSpeed;
      switch (deltaMode) {
        case 2:
          // Zoom in pages
          speed *= 10;
          break;
        case 1:
          // Zoom in lines
          speed *= 3;
          break;
      }
      let step = Math.pow(0.95, speed);
      if (delta < 0) {
        step = 1 / step;
      }
      _this.object.zoom *= step;
      _this.object.updateProjectionMatrix();
      _this.projectionChanged = true;
    } else {
      switch (deltaMode) {
        case 2:
          // Zoom in pages
          _zoomStart.y -= delta * 0.025;
          break;
        case 1:
          // Zoom in lines
          _zoomStart.y -= delta * 0.01;
          break;
        default:
          // undefined, 0, assume pixels
          _zoomStart.y -= delta * 0.00025;
          break;
      }
      _this.dispatchEvent(startEvent);
      _this.dispatchEvent(endEvent);
    }
  };

  function touchstart(event) {
    if (_this.enabled === false) return;

    switch (event.touches.length) {
      case 1:
        _state = STATE.TOUCH_ROTATE;
        _moveCurr.copy(getMouseOnCircle(event.touches[0].pageX, event.touches[0].pageY));
        _movePrev.copy(_moveCurr);
        break;
      default: { // 2 or more
        _state = STATE.TOUCH_ZOOM_PAN;
        const dx = event.touches[0].pageX - event.touches[1].pageX;
        const dy = event.touches[0].pageY - event.touches[1].pageY;
        _touchZoomDistanceEnd = _touchZoomDistanceStart = Math.sqrt(dx * dx + dy * dy);

        const x = (event.touches[0].pageX + event.touches[1].pageX) / 2;
        const y = (event.touches[0].pageY + event.touches[1].pageY) / 2;
        _panStart.copy(getMouseOnScreen(x, y));
        _panEnd.copy(_panStart);
        break;
      }
    }

    _this.dispatchEvent(startEvent);
  }

  function touchmove(event) {
    if (_this.enabled === false) return;

    event.preventDefault();
    event.stopPropagation();

    switch (event.touches.length) {
      case 1:
        _movePrev.copy(_moveCurr);
        _moveCurr.copy(getMouseOnCircle(event.touches[0].pageX, event.touches[0].pageY));
        break;
      default: { // 2 or more
        const dx = event.touches[0].pageX - event.touches[1].pageX;
        const dy = event.touches[0].pageY - event.touches[1].pageY;
        _touchZoomDistanceEnd = Math.sqrt(dx * dx + dy * dy);

        const x = (event.touches[0].pageX + event.touches[1].pageX) / 2;
        const y = (event.touches[0].pageY + event.touches[1].pageY) / 2;
        _panEnd.copy(getMouseOnScreen(x, y));
        break;
      }
    }
  }

  function touchend(event) {
    if (_this.enabled === false) return;

    switch (event.touches.length) {
      case 0:
        _state = STATE.NONE;
        break;
      case 1:
        _state = STATE.TOUCH_ROTATE;
        _moveCurr.copy(getMouseOnCircle(event.touches[0].pageX, event.touches[0].pageY));
        _movePrev.copy(_moveCurr);
        break;
    }

    _this.dispatchEvent(endEvent);
  }

  function contextmenu(event) {
    if (_this.enabled === false) return;

    event.preventDefault();
  }

  this.dispose = function () {
    this.domElement.removeEventListener('contextmenu', contextmenu, false);
    this.domElement.removeEventListener('mousedown', mousedown, false);
    this.domElement.removeEventListener('wheel', mousewheel, false);

    this.domElement.removeEventListener('touchstart', touchstart, false);
    this.domElement.removeEventListener('touchend', touchend, false);
    this.domElement.removeEventListener('touchmove', touchmove, false);

    document.removeEventListener('mousemove', mousemove, false);
    document.removeEventListener('mouseup', mouseup, false);

    window.removeEventListener('keydown', keydown, false);
    window.removeEventListener('keyup', keyup, false);
  };

  this.domElement.addEventListener('contextmenu', contextmenu, false);
  this.domElement.addEventListener('mousedown', mousedown, false);
  this.domElement.addEventListener('wheel', mousewheel, false);

  this.domElement.addEventListener('touchstart', touchstart, false);
  this.domElement.addEventListener('touchend', touchend, false);
  this.domElement.addEventListener('touchmove', touchmove, false);

  window.addEventListener('keydown', keydown, false);
  window.addEventListener('keyup', keyup, false);

  this.handleResize();
}

CADTrackballControls.prototype = Object.create(THREE.EventDispatcher.prototype);
CADTrackballControls.prototype.constructor = CADTrackballControls;

/*
Rotation simulation with mouse move events

if (window.controls) {
  window.controls.setState(0);  // Set state to ROTATE

  let x = 0;  // Initial x-coordinate for y-axis rotation
  let y = 0;  // Initial y-coordinate for x-axis rotation
  const speed = 1;  // Speed of rotation in pixels per frame
  const framesForFullRotationX = window.innerHeight / speed; // Number of frames to complete 360 rotation around x-axis
  const framesForFullRotationY = window.innerWidth / speed;  // Number of frames to complete 360 rotation around y-axis

  let currentFrameX = 0;
  let currentFrameY = 0;

  function rotateContinuouslyX() {
    // Increment the y-coordinate to simulate rotation around the x-axis
    y += speed;
    currentFrameX++;

    // Simulate the mouse move to the new position (y changes, x is constant)
    window.controls.simulateMouseMove(x, y);

    // Check if a full 360 rotation is done around x-axis
    if (currentFrameX >= framesForFullRotationX) {
      currentFrameX = 0;
      setTimeout(rotateContinuouslyY, 1000);  // Start y-axis rotation after a brief pause
    } else {
      // Request the next frame for continuous rotation
      requestAnimationFrame(rotateContinuouslyX);
    }
  }

  function rotateContinuouslyY() {
    // Increment the x-coordinate to simulate rotation around the y-axis
    x += speed;
    currentFrameY++;

    // Simulate the mouse move to the new position (x changes, y is constant)
    window.controls.simulateMouseMove(x, y);

    // Check if a full 360 rotation is done around y-axis
    if (currentFrameY >= framesForFullRotationY) {
      console.log('Both rotations complete');
    } else {
      // Request the next frame for continuous rotation
      requestAnimationFrame(rotateContinuouslyY);
    }
  }

  // Start the rotation around the x-axis
  rotateContinuouslyX();

} else {
  console.error('controls is not defined');
}




Rotation simulation with roteateCamera and animate

if (window.controls) {
  // Set initial and current positions for rotation
  window.controls.setMovePrev(0, 0);  // Initial mouse position
  window.controls.setMoveCurr(10, 40);  // New mouse position
  
  // Set the state to ROTATE
  window.controls.setState(0); // 0 corresponds to ROTATE in the STATE object
  
  // Call the rotateCamera method
  window.controls.rotateCamera();
  
  // Update the camera
  window.controls.evaluate();

  window.animate();  
} else {
  console.error('controls is not defined');
}
*/