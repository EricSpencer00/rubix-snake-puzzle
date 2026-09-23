// Lightweight regressions for the exact geometry shipped in the static page.
// Run: node --test tests/snake-page.test.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const THREE = require('../docs/vendor/three.min.js');

const html = fs.readFileSync(path.join(__dirname, '../docs/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const context = vm.createContext({THREE});
vm.runInContext(script.slice(script.indexOf('const BALL_CONFIG'), script.indexOf('\nheroSnake();')), context);
const {calculateLatticePieces, detectCollisions, latticeVector, createLatticePrismGeometry, buildSnakeGeometry} = context;
const ball = Array.from(vm.runInContext('BALL_CONFIG', context));
const straight = Array(23).fill(0);
const shared = (a, b) => a.vertices.filter(p => b.vertices.some(q => p.every((v, i) => v === q[i])));
const vector = p => new THREE.Vector3(...p);
const configurations = [straight, ball];
for (let joint = 0; joint < 23; joint++) {
  for (let turn = 0; turn < 4; turn++) {
    const config = [...ball];
    config[joint] = turn;
    configurations.push(config);
  }
}

test('the shipped page script parses and uses the bundled renderer', () => {
  new vm.Script(script);
  assert.match(html, /src="vendor\/three.min.js"/);
  assert.ok(THREE.ExtrudeGeometry);
});

test('the complete page starts both renderers in browser script order', () => {
  const elements = new Map();
  const frames = [];
  const scenes = [];
  const element = () => ({
    children: [], innerHTML: '', style: {}, classList: {toggle() {}},
    parentElement: {clientWidth: 1280, clientHeight: 720},
    appendChild(child) { this.children.push(child); },
    addEventListener() {}, setAttribute() {},
    getBoundingClientRect() { return {width: 560, height: 420}; },
  });
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, element());
      return elements.get(id);
    },
    createElement: element,
    querySelectorAll(selector) {
      if (selector !== '#joint-controls .rot-btn') return [];
      return elements.get('joint-controls').children.flatMap(row =>
        [...row.innerHTML.matchAll(/data-joint="(\d+)" data-rot="(\d+)"/g)].map(match => ({
          ...element(), dataset: {joint: match[1], rot: match[2]},
        })));
    },
  };
  const sandbox = vm.createContext({
    THREE: {...THREE, WebGLRenderer: class {
      setPixelRatio() {} setSize() {} setClearColor() {}
      render(scene) { scenes.push(scene); }
    }},
    document,
    window: {devicePixelRatio: 1, addEventListener() {}, matchMedia() { return {matches: false}; }},
    ResizeObserver: class {observe() {}},
    IntersectionObserver: class {observe() {}},
    requestAnimationFrame(callback) { frames.push(callback); },
  });
  // Execute the actual page, including startup calls, rather than just loading
  // selected functions. This catches the live site's pre-initialization crash.
  vm.runInContext(script, sandbox);
  assert.equal(frames.length, 2);
  frames.splice(0).forEach(frame => frame(0));
  assert.equal(scenes.length, 2);
  assert.ok(scenes.every(scene => scene.children.some(child => child.isGroup && child.children.length === 24)));
  assert.equal(document.querySelectorAll('#joint-controls .rot-btn').length, 92);
  assert.match(elements.get('builder-status').innerHTML, /All 24 prisms are clear/);
});

test('the page separates published full-size totals from its local model checks', () => {
  assert.match(html, /Peter Aylett's corrected exhaustive search, not a proof in this repository/);
  assert.match(html, /Python cell-search counts for 2–14 wedges/);
  assert.match(html, /builder uses a separate half-cube prism overlap check/);
  assert.doesNotMatch(html, /First formal verification|Coq \+ Python|Verified counts/);
});

test('every quarter-turn joins full square faces, not points or edges', () => {
  for (const config of configurations) {
    const pieces = calculateLatticePieces(24, config);
    for (const piece of pieces) {
      assert.equal(new Set(piece.vertices.map(p => p.join(','))).size, 6);
      const [a, b, c] = piece.basis.map(vector);
      assert.equal(a.lengthSq(), 1);
      assert.equal(b.lengthSq(), 1);
      assert.equal(c.lengthSq(), 1);
      assert.ok(a.dot(b) === 0);
      assert.ok(a.dot(c) === 0);
      assert.ok(b.dot(c) === 0);
    }
    for (let i = 0; i < 23; i++) {
      const face = shared(pieces[i], pieces[i + 1]);
      assert.equal(face.length, 4, `joint ${i + 1}, config ${config}`);
      const distances = Array.from(face.slice(1), p => vector(p).distanceToSquared(vector(face[0]))).sort();
      assert.deepEqual(distances, [1, 1, 2]);
    }
  }
});

test('straight snake has a continuous bar envelope with no collisions', () => {
  const pieces = calculateLatticePieces(24, straight);
  const bounds = new THREE.Box3().setFromPoints(pieces.flatMap(p => p.vertices.map(latticeVector)));
  const size = bounds.getSize(new THREE.Vector3());
  assert.ok(Math.abs(size.x - 25 * Math.SQRT1_2) < 1e-8);
  assert.ok(Math.abs(size.y - Math.SQRT1_2) < 1e-8);
  assert.equal(size.z, 1);
  assert.equal(detectCollisions(24, straight).size, 0);
});

test('ball is closed, compact, and collision-free (catches the J21 typo)', () => {
  const pieces = calculateLatticePieces(24, ball);
  assert.equal(shared(pieces[0], pieces[23]).length, 4);
  const bounds = new THREE.Box3().setFromPoints(pieces.flatMap(p => p.vertices.map(vector)));
  assert.deepEqual(bounds.getSize(new THREE.Vector3()).toArray(), [3, 3, 3]);
  assert.equal(detectCollisions(24, ball).size, 0);
  const broken = [...ball];
  broken[20] = 0;
  const brokenPieces = calculateLatticePieces(24, broken);
  assert.notEqual(shared(brokenPieces[0], brokenPieces[23]).length, 4);
  assert.ok(detectCollisions(24, Array(23).fill(2)).size > 0);
});

test('rendered plastic is closed, outward-facing, and inside each physical prism', () => {
  for (const config of [straight, ball, Array(23).fill(1)]) {
    for (const piece of calculateLatticePieces(24, config)) {
      const vertices = piece.vertices.map(latticeVector);
      const geometry = createLatticePrismGeometry(vertices);
      const position = geometry.getAttribute('position');
      const normal = geometry.getAttribute('normal');
      const origin = vertices[0];
      const axes = [1, 2, 3].map(i => vertices[i].clone().sub(origin));
      const center = vertices.reduce((sum, p) => sum.add(p), new THREE.Vector3()).multiplyScalar(1 / 6);
      let volume = 0;
      const edges = new Map();
      for (let i = 0; i < position.count; i++) {
        const p = new THREE.Vector3().fromBufferAttribute(position, i);
        const local = p.clone().sub(origin);
        const [x, y, z] = axes.map(axis => local.dot(axis));
        assert.ok(x >= -1e-5 && y >= -1e-5 && x + y <= 1 + 1e-5 && z >= -1e-5 && z <= 1 + 1e-5);
        assert.ok(new THREE.Vector3().fromBufferAttribute(normal, i).dot(p.clone().sub(center)) > 0);
        if (i % 3 !== 0) continue;
        const triangle = [0, 1, 2].map(j => new THREE.Vector3().fromBufferAttribute(position, i + j));
        volume += triangle[0].dot(triangle[1].clone().cross(triangle[2])) / 6;
        const keys = triangle.map(v => v.toArray().map(n => n.toFixed(4)).join(','));
        for (let j = 0; j < 3; j++) {
          const key = [keys[j], keys[(j + 1) % 3]].sort().join('|');
          edges.set(key, (edges.get(key) ?? 0) + 1);
        }
      }
      assert.ok(volume > 0.45 && volume < 0.5, `prism volume ${volume}`);
      assert.ok([...edges.values()].every(count => count === 2), 'each mesh edge has two faces');
      geometry.dispose();
    }
  }
});

test('rebuilding frees every old mesh and never accumulates hidden hardware', () => {
  const group = new THREE.Group();
  buildSnakeGeometry(group, straight, 0xc8883a, 0xede8d8);
  assert.equal(group.children.length, 24);
  let disposed = 0;
  group.children.forEach(mesh => {
    mesh.geometry.addEventListener('dispose', () => disposed++);
    mesh.material.addEventListener('dispose', () => disposed++);
  });
  buildSnakeGeometry(group, ball, 0xc8883a, 0xede8d8);
  assert.equal(disposed, 48);
  assert.equal(group.children.length, 24);
});

test('camera keeps every prism in frame at portrait and landscape sizes', () => {
  vm.runInContext(script.slice(script.indexOf('function fitBuilderCamera()'), script.indexOf('(function initBuilder()')), context);
  for (const config of [straight, ball]) {
    const group = new THREE.Group();
    buildSnakeGeometry(group, config, 0xc8883a, 0xede8d8);
    for (const aspect of [0.5, 1, 4 / 3, 2]) {
      const camera = new THREE.PerspectiveCamera(35, aspect, 0.1, 100);
      context.builderGroup = group;
      context.builderCamera = camera;
      context.fitBuilderCamera();
      camera.updateMatrixWorld();
      for (const y of [0, 0.6, Math.PI / 2]) {
        group.rotation.set(0.4, y, 0);
        group.updateMatrixWorld(true);
        for (const mesh of group.children) {
          const positions = mesh.geometry.getAttribute('position');
          for (let i = 0; i < positions.count; i++) {
            const point = new THREE.Vector3().fromBufferAttribute(positions, i).applyMatrix4(mesh.matrixWorld).project(camera);
            assert.ok(Math.abs(point.x) < 1 && Math.abs(point.y) < 1 && Math.abs(point.z) < 1);
          }
        }
      }
    }
  }
});

test('repeated joint clicks keep one handler, all 23 controls, and keyboard focus targets', () => {
  const elements = new Map();
  function element() {
    return {
      children: [], buttons: [], handlers: {}, checked: false, textContent: '', classList: {toggle() {}},
      setAttribute() {}, appendChild(child) { this.children.push(child); },
      addEventListener(event, callback) { (this.handlers[event] ??= []).push(callback); },
      getBoundingClientRect() { return {width: 560, height: 420}; },
      get innerHTML() { return this._innerHTML; },
      set innerHTML(value) {
        this._innerHTML = value;
        this.children = [];
        this.buttons = [...value.matchAll(/data-joint="(\d+)" data-rot="(\d+)"/g)].map(match => ({
          dataset: {joint: match[1], rot: match[2]},
          classList: {toggle() {}}, setAttribute() {},
        }));
      },
    };
  }
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, element());
      return elements.get(id);
    },
    createElement: element,
    querySelectorAll() { return elements.get('joint-controls').children.flatMap(row => row.buttons); },
  };
  const sandbox = vm.createContext({
    THREE: {...THREE, WebGLRenderer: class {setPixelRatio() {} setSize() {} setClearColor() {}}},
    document, window: {devicePixelRatio: 2},
    ResizeObserver: class {observe() {}}, requestAnimationFrame() {},
    addSnakeLighting() {},
  });
  vm.runInContext(script.slice(script.indexOf('const BALL_CONFIG'), script.indexOf('\nheroSnake();')), sandbox);
  vm.runInContext(script.slice(script.indexOf('const NUM_JOINTS'), script.indexOf('// ─── SCROLL FADE IN')), sandbox);
  const controls = document.getElementById('joint-controls');
  const lastButton = document.querySelectorAll().at(-1);
  assert.equal(document.querySelectorAll().length, 92);
  for (let i = 0; i < 50; i++) {
    const button = document.querySelectorAll()[i % 92];
    for (const handler of [...controls.handlers.click]) handler({target: {closest: () => button}});
    assert.equal(controls.handlers.click.length, 1);
    assert.equal(vm.runInContext('builderGroup.children.length', sandbox), 24);
  }
  controls.handlers.click[0]({target: {closest: () => lastButton}});
  const lastTurn = String(vm.runInContext('builderConfig[22]', sandbox));
  assert.ok(document.querySelectorAll().some(button => button.dataset.joint === '22' && button.dataset.rot === lastTurn));
  assert.equal(vm.runInContext('detectCollisions(24, builderConfig).size', sandbox), 0);
  assert.equal(document.querySelectorAll().at(-1), lastButton, 'controls remain mounted');

  const collisionSwitch = document.getElementById('prevent-collisions');
  assert.equal(collisionSwitch.checked, true, 'overlap prevention starts on');
  vm.runInContext('ballSnake()', sandbox);
  const ballConfig = Array.from(vm.runInContext('builderConfig', sandbox));
  const collidingTurn = document.querySelectorAll().find(button => button.dataset.joint === '0' && button.dataset.rot === '0');
  controls.handlers.click[0]({target: {closest: () => collidingTurn}});
  assert.deepEqual(Array.from(vm.runInContext('builderConfig', sandbox)), ballConfig, 'a colliding turn is not applied');
  assert.match(document.getElementById('builder-status').innerHTML, /Turn skipped/);

  for (let i = 0; i < 5; i++) {
    vm.runInContext('randomizeSnake()', sandbox);
    assert.equal(vm.runInContext('detectCollisions(24, builderConfig).size', sandbox), 0, 'random valid shapes stay clear');
  }

  collisionSwitch.checked = false;
  collisionSwitch.handlers.change[0]({currentTarget: collisionSwitch});
  vm.runInContext('builderConfig = Array(23).fill(2); updateBuilder()', sandbox);
  assert.ok(vm.runInContext('detectCollisions(24, builderConfig).size', sandbox) > 0, 'turning the switch off allows overlap');
  collisionSwitch.checked = true;
  collisionSwitch.handlers.change[0]({currentTarget: collisionSwitch});
  assert.equal(vm.runInContext('detectCollisions(24, builderConfig).size', sandbox), 0, 'turning it on repairs an overlapping shape');
  assert.match(document.getElementById('builder-status').innerHTML, /adjusted to clear/);
});

test('hero animation moves but never sweeps through the title or out of frame', () => {
  for (const [width, height] of [[1280, 720], [390, 844], [768, 1024]]) {
    let frame, rendered;
    const sandbox = vm.createContext({
      THREE: {...THREE, WebGLRenderer: class {
        setPixelRatio() {} setSize() {}
        render(scene, camera) { rendered = {scene, camera}; }
      }},
      document: {getElementById() { return {parentElement: {clientWidth: width, clientHeight: height}}; }},
      window: {devicePixelRatio: 2, addEventListener() {}}, reducedMotion: {matches: false},
      requestAnimationFrame(callback) { frame = callback; }, addSnakeLighting() {},
    });
    vm.runInContext(script.slice(script.indexOf('const BALL_CONFIG'), script.indexOf('\nheroSnake();')), sandbox);
    vm.runInContext(script.slice(script.indexOf('function heroSnake()'), script.indexOf('// A Rubik\'s Snake')), sandbox);
    sandbox.heroSnake();
    const yaw = new Set();
    for (let time = 0; time < 120000; time += 1000) {
      frame(time);
      const {scene, camera} = rendered;
      scene.updateMatrixWorld(true);
      camera.updateMatrixWorld();
      const group = scene.children[0];
      yaw.add(group.rotation.y);
      for (const mesh of group.children) {
        const positions = mesh.geometry.getAttribute('position');
        for (let i = 0; i < positions.count; i++) {
          const point = new THREE.Vector3().fromBufferAttribute(positions, i).applyMatrix4(mesh.matrixWorld).project(camera);
          assert.ok(Math.abs(point.x) < 1 && Math.abs(point.y) < 1, 'model stays in view');
          assert.ok((1 - point.y) * height / 2 < height * 0.53, `model stays above title: ${width}x${height}, time ${time}, y ${(1 - point.y) * height / 2}`);
        }
      }
    }
    assert.ok(yaw.size > 1, 'animation changes the viewing angle');
  }
});
