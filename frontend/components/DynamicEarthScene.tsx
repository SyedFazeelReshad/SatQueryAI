'use client';

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function DynamicEarthScene() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
    camera.position.set(0, 0, 7.8);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(renderer.domElement);

    const textureLoader = new THREE.TextureLoader();

    // Earth Textures
    const earthDayMap = textureLoader.load(
      'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_atmos_2048.jpg'
    );
    const earthSpecMap = textureLoader.load(
      'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_specular_2048.jpg'
    );
    const earthCloudsMap = textureLoader.load(
      'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_clouds_1024.png'
    );

    // 1. SPIRAL GALAXY GENERATION (Milky Way / Nebula Backdrop)
    const galaxyParams = {
      count: 4500,
      size: 0.14,
      radius: 42,
      branches: 3,
      spin: 1.2,
      randomness: 0.45,
      power: 3.5,
      insideColor: '#38bdf8',
      outsideColor: '#6366f1',
    };

    const galaxyGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(galaxyParams.count * 3);
    const colors = new Float32Array(galaxyParams.count * 3);

    const colorInside = new THREE.Color(galaxyParams.insideColor);
    const colorOutside = new THREE.Color(galaxyParams.outsideColor);

    for (let i = 0; i < galaxyParams.count; i++) {
      const i3 = i * 3;
      const r = Math.random() * galaxyParams.radius;
      const spinAngle = r * galaxyParams.spin;
      const branchAngle = ((i % galaxyParams.branches) * 2 * Math.PI) / galaxyParams.branches;

      const randomX = Math.pow(Math.random(), galaxyParams.power) * (Math.random() < 0.5 ? 1 : -1) * galaxyParams.randomness * r;
      const randomY = Math.pow(Math.random(), galaxyParams.power) * (Math.random() < 0.5 ? 1 : -1) * (galaxyParams.randomness * 0.4) * r;
      const randomZ = Math.pow(Math.random(), galaxyParams.power) * (Math.random() < 0.5 ? 1 : -1) * galaxyParams.randomness * r;

      positions[i3] = Math.cos(branchAngle + spinAngle) * r + randomX;
      positions[i3 + 1] = randomY - 2;
      positions[i3 + 2] = Math.sin(branchAngle + spinAngle) * r + randomZ - 18;

      const mixedColor = colorInside.clone();
      mixedColor.lerp(colorOutside, r / galaxyParams.radius);
      colors[i3] = mixedColor.r;
      colors[i3 + 1] = mixedColor.g;
      colors[i3 + 2] = mixedColor.b;
    }

    galaxyGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    galaxyGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const galaxyMat = new THREE.PointsMaterial({
      size: galaxyParams.size,
      sizeAttenuation: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexColors: true,
      transparent: true,
      opacity: 0.55,
    });

    const galaxy = new THREE.Points(galaxyGeo, galaxyMat);
    galaxy.rotation.x = Math.PI / 4.5;
    scene.add(galaxy);

    // 2. BACKGROUND COSMIC STARS FIELD
    const starCount = 2000;
    const starGeo = new THREE.BufferGeometry();
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      starPos[i] = (Math.random() - 0.5) * 160;
      starPos[i + 1] = (Math.random() - 0.5) * 160;
      starPos[i + 2] = -Math.random() * 80 - 10;
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({
      size: 0.15,
      color: 0xffffff,
      transparent: true,
      opacity: 0.75,
    });
    const starField = new THREE.Points(starGeo, starMat);
    scene.add(starField);

    // 3. EARTH & ATMOSPHERE
    const earthGroup = new THREE.Group();
    earthGroup.position.set(0, -0.25, 0);
    earthGroup.rotation.z = (23.4 * Math.PI) / 180;
    scene.add(earthGroup);

    const earthGeo = new THREE.SphereGeometry(2.15, 64, 64);
    const earthMat = new THREE.MeshStandardMaterial({
      map: earthDayMap,
      roughnessMap: earthSpecMap,
      roughness: 0.65,
      metalness: 0.12,
    });
    const earthMesh = new THREE.Mesh(earthGeo, earthMat);
    earthGroup.add(earthMesh);

    const cloudGeo = new THREE.SphereGeometry(2.175, 64, 64);
    const cloudMat = new THREE.MeshStandardMaterial({
      map: earthCloudsMap,
      transparent: true,
      opacity: 0.38,
      blending: THREE.AdditiveBlending,
    });
    const cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
    earthGroup.add(cloudMesh);

    const atmosphereGeo = new THREE.SphereGeometry(2.26, 64, 64);
    const atmosphereMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.68 - dot(vNormal, vec3(0, 0, 1.0)), 2.6);
          gl_FragColor = vec4(0.2, 0.75, 1.0, 1.0) * intensity * 1.35;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
    });
    const atmosphereMesh = new THREE.Mesh(atmosphereGeo, atmosphereMat);
    scene.add(atmosphereMesh);

    // 4. SATELLITE ORBIT
    const orbitRadius = 3.65;
    const orbitCurve = new THREE.EllipseCurve(0, 0, orbitRadius, orbitRadius * 0.92, 0, 2 * Math.PI, false, 0);
    const orbitPoints = orbitCurve.getPoints(128);
    const orbitGeo = new THREE.BufferGeometry().setFromPoints(orbitPoints.map((p) => new THREE.Vector3(p.x, 0, p.y)));
    const orbitMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.3,
    });
    const orbitLine = new THREE.LineLoop(orbitGeo, orbitMat);
    orbitLine.rotation.x = Math.PI / 2.7;
    orbitLine.rotation.z = Math.PI / 6;
    scene.add(orbitLine);

    const satelliteGroup = new THREE.Group();
    const busGeo = new THREE.BoxGeometry(0.16, 0.11, 0.11);
    const busMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9, roughness: 0.2 });
    const busMesh = new THREE.Mesh(busGeo, busMat);
    satelliteGroup.add(busMesh);

    const panelGeo = new THREE.BoxGeometry(0.35, 0.014, 0.14);
    const panelMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.75, roughness: 0.25 });
    const p1 = new THREE.Mesh(panelGeo, panelMat);
    p1.position.set(-0.25, 0, 0);
    const p2 = new THREE.Mesh(panelGeo, panelMat);
    p2.position.set(0.25, 0, 0);
    satelliteGroup.add(p1, p2);

    const lensGeo = new THREE.SphereGeometry(0.028, 16, 16);
    const lensMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    const lens = new THREE.Mesh(lensGeo, lensMat);
    lens.position.set(0, -0.07, 0);
    satelliteGroup.add(lens);

    scene.add(satelliteGroup);

    // Lights
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.6);
    dirLight.position.set(9, 5, 8);
    scene.add(dirLight);

    const ambientLight = new THREE.AmbientLight(0x0f172a, 1.4);
    scene.add(ambientLight);

    // Mouse Interaction
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let rotX = 0;
    let rotY = 0;
    let orbitAngle = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        rotY += (e.clientX - prevX) * 0.004;
        rotX += (e.clientY - prevY) * 0.004;
        prevX = e.clientX;
        prevY = e.clientY;
      }
    };
    const onMouseUp = () => { isDragging = false; };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      earthMesh.rotation.y += 0.0015;
      cloudMesh.rotation.y += 0.002;
      earthGroup.rotation.y += (rotY - earthGroup.rotation.y) * 0.04;
      earthGroup.rotation.x += (rotX - earthGroup.rotation.x) * 0.04;

      // Subtle slow rotation of the galaxy in deep space
      galaxy.rotation.y += 0.0003;
      starField.rotation.y += 0.0001;

      orbitAngle += 0.011;
      const x = Math.cos(orbitAngle) * orbitRadius;
      const z = Math.sin(orbitAngle) * (orbitRadius * 0.92);
      const y = Math.sin(orbitAngle * 1.4) * 0.65 - 0.25;

      const pos = new THREE.Vector3(x, y, z);
      pos.applyAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI / 2.7);
      pos.applyAxisAngle(new THREE.Vector3(0, 0, 1), Math.PI / 6);

      satelliteGroup.position.copy(pos);
      satelliteGroup.lookAt(earthMesh.position);

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div 
      ref={mountRef} 
      className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing pointer-events-auto" 
      title="Click and drag to spin Earth"
    />
  );
}
