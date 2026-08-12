/* ==========================================================================
   SNEAKER PULSE COMMAND CENTER - THREE.JS 3D PARTICLE RADAR & LASER SCANNER
   ========================================================================== */

(function () {
  const container = document.getElementById("webgl-container");
  if (!container || typeof THREE === "undefined") return;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    container.style.display = "none";
    return;
  }

  let scene, camera, renderer, particleSystem, scanBeamPlane;
  let mouseX = 0, mouseY = 0;
  let windowHalfX = window.innerWidth / 2;
  let windowHalfY = window.innerHeight / 2;
  let animationFrameId = null;
  let isScanningBeamActive = false;
  let scanBeamY = 400;

  function init() {
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x060709, 0.0015);

    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 3000);
    camera.position.z = 800;

    // Generate Particle Matrix Points
    const particleCount = window.innerWidth < 768 ? 600 : 1600;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const colorNeonRed = new THREE.Color("#ff1e42");
    const colorDarkRed = new THREE.Color("#800010");

    for (let i = 0; i < particleCount; i++) {
      const radius = 400 + Math.random() * 300;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      const mixedColor = colorNeonRed.clone().lerp(colorDarkRed, Math.random());
      colors[i * 3] = mixedColor.r;
      colors[i * 3 + 1] = mixedColor.g;
      colors[i * 3 + 2] = mixedColor.b;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    // Canvas Texture for Glow
    const canvas = document.createElement("canvas");
    canvas.width = 16;
    canvas.height = 16;
    const ctx = canvas.getContext("2d");
    const grad = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
    grad.addColorStop(0, "rgba(255, 255, 255, 1)");
    grad.addColorStop(0.4, "rgba(255, 30, 66, 0.8)");
    grad.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 16, 16);

    const texture = new THREE.CanvasTexture(canvas);

    const material = new THREE.PointsMaterial({
      size: 14,
      map: texture,
      vertexColors: true,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    particleSystem = new THREE.Points(geometry, material);
    scene.add(particleSystem);

    // Laser Beam Scanning Plane
    const scanGeo = new THREE.PlaneGeometry(1200, 10);
    const scanMat = new THREE.MeshBasicMaterial({
      color: 0xff1e42,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide
    });
    scanBeamPlane = new THREE.Mesh(scanGeo, scanMat);
    scanBeamPlane.position.y = 400;
    scene.add(scanBeamPlane);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    document.addEventListener("mousemove", onDocumentMouseMove, { passive: true });
    window.addEventListener("resize", onWindowResize);
    document.addEventListener("visibilitychange", onVisibilityChange);

    animate();
  }

  function onDocumentMouseMove(event) {
    mouseX = (event.clientX - windowHalfX) * 0.3;
    mouseY = (event.clientY - windowHalfY) * 0.3;
  }

  function onWindowResize() {
    windowHalfX = window.innerWidth / 2;
    windowHalfY = window.innerHeight / 2;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function onVisibilityChange() {
    if (document.hidden) {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    } else {
      animate();
    }
  }

  function animate() {
    animationFrameId = requestAnimationFrame(animate);

    camera.position.x += (mouseX - camera.position.x) * 0.03;
    camera.position.y += (-mouseY - camera.position.y) * 0.03;
    camera.lookAt(scene.position);

    if (particleSystem) {
      particleSystem.rotation.y += 0.0015;
      particleSystem.rotation.x += 0.0005;
    }

    if (isScanningBeamActive && scanBeamPlane) {
      scanBeamY -= 12;
      scanBeamPlane.position.y = scanBeamY;
      scanBeamPlane.material.opacity = 0.6;
      if (scanBeamY < -400) {
        scanBeamY = 400;
        isScanningBeamActive = false;
        scanBeamPlane.material.opacity = 0.0;
      }
    }

    renderer.render(scene, camera);
  }

  window.triggerLaserScan = function () {
    isScanningBeamActive = true;
    scanBeamY = 400;
  };

  window.addEventListener("DOMContentLoaded", init);
})();
