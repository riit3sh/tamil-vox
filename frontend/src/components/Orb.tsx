"use client";

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere } from '@react-three/drei';
import * as THREE from 'three';

const vertexShader = `
uniform float uTime;
uniform float uAmplitude;
varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vWorldPosition;

// Simple 3D noise function
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
  const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy) );
  vec3 x0 = v - i + dot(i, C.xxx) ;
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min( g.xyz, l.zxy );
  vec3 i2 = max( g.xyz, l.zxy );
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute( permute( permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0 ))
           + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));
  float n_ = 0.142857142857;
  vec3  ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_ );
  vec4 x = x_ *ns.x + ns.yyyy;
  vec4 y = y_ *ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4( x.xy, y.xy );
  vec4 b1 = vec4( x.zw, y.zw );
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;
  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;
  vec4 m = max(0.5 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
}

void main() {
  vUv = uv;
  // Transform normal to world space for correct Fresnel during rotation
  vNormal = normalize(normalMatrix * normal);
  
  // Layered noise for more aggressive craters and flames
  float noise1 = snoise(vec3(position.x * 4.0, position.y * 4.0 + uTime * 0.8, position.z * 4.0));
  float noise2 = snoise(vec3(position.x * 6.0 - uTime * 0.5, position.y * 6.0, position.z * 6.0 + uTime * 0.5));
  
  float combinedNoise = (noise1 * 0.6) + (noise2 * 0.4);
  
  // Use abs() to create sharp outward flames, and normal noise for craters
  float displacement = (combinedNoise > 0.0) ? (combinedNoise * combinedNoise) : combinedNoise;
  
  vec3 newPosition = position + normal * (displacement * uAmplitude);
  vPosition = newPosition;
  
  // Calculate world position for correct camera view direction
  vec4 worldPos = modelMatrix * vec4(newPosition, 1.0);
  vWorldPosition = worldPos.xyz;
  
  gl_Position = projectionMatrix * viewMatrix * worldPos;
}
`;

const fragmentShader = `
uniform float uTime;
uniform vec3 uColorBase;
uniform vec3 uColorGlow;
uniform float uIntensity;

varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vWorldPosition;

// Noise function duplicated for fragment volumetric effect
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
  const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy) );
  vec3 x0 = v - i + dot(i, C.xxx) ;
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min( g.xyz, l.zxy );
  vec3 i2 = max( g.xyz, l.zxy );
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute( permute( permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0 ))
           + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));
  float n_ = 0.142857142857;
  vec3  ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_ );
  vec4 x = x_ *ns.x + ns.yyyy;
  vec4 y = y_ *ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4( x.xy, y.xy );
  vec4 b1 = vec4( x.zw, y.zw );
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;
  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;
  vec4 m = max(0.5 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
}

void main() {
  // Edge glow effect (Fresnel) - now correctly using world space so rotation doesn't break it!
  vec3 viewDirection = normalize(cameraPosition - vWorldPosition);
  float fresnel = dot(viewDirection, vNormal);
  fresnel = clamp(1.0 - fresnel, 0.0, 1.0);
  fresnel = pow(fresnel, 3.5); // sharper edge
  
  // Layered volumetric noise
  // We use 4.0 and 6.0 to match the vertex shader so the patches are spread all over the orb
  // The time multipliers are heavily reduced so the patches morph very slowly instead of disappearing
  // STABLE SPHERE COORDS
  vec3 sphereCoords = normalize(vPosition);

  // Anchored crater topology
  float noise1 = snoise(vec3(
    sphereCoords.x * 4.0,
    sphereCoords.y * 4.0 + uTime * 0.08,
    sphereCoords.z * 4.0
  ));

  float noise2 = snoise(vec3(
    sphereCoords.x * 7.0 - uTime * 0.04,
    sphereCoords.y * 7.0,
    sphereCoords.z * 7.0 + uTime * 0.08
  ));
  float layeredNoise = (noise1 * 0.7) + (noise2 * 0.3);
  
  // Slow plasma pulse
  float pulse = sin(uTime * 1.2) * 0.5 + 0.5;

  // Sharpen crater/plasma separation
  layeredNoise = pow(abs(layeredNoise), 1.4) * sign(layeredNoise);

  // Plasma mask
  float plasmaMask = smoothstep(
    0.15,
    0.75,
    layeredNoise + pulse * 0.15
  );

  // Remove the dark voids completely and use dim plasma instead
  vec3 craterColor = uColorGlow * 0.2;

  // Bright plasma
  vec3 plasmaColor = uColorGlow;

  // Preserve dark regions permanently
  vec3 innerPlasma = mix(
    craterColor,
    plasmaColor,
    plasmaMask
  );

  // Edge glow ONLY at edges
  vec3 edgeGlow = uColorGlow * fresnel * (uIntensity * 0.35);

  // Subsurface energy leak
  float subsurface = smoothstep(-0.4, 0.4, layeredNoise) * 0.15;

  // Final color
  vec3 finalColor =
    innerPlasma +
    edgeGlow +
    (uColorGlow * subsurface);

  // Better alpha preservation
  float alpha =
    smoothstep(-0.3, 0.7, layeredNoise) * 0.65 +
    fresnel * 0.35 +
    0.35;

  alpha = clamp(alpha, 0.0, 1.0);

  gl_FragColor = vec4(finalColor, alpha);
}
`;

function OrbMesh({ state = 'idle' }: { state: 'idle' | 'listening' | 'speaking' }) {
  const mesh = useRef<THREE.Mesh>(null);
  
  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uAmplitude: { value: 0.2 },
    uColorBase: { value: new THREE.Color("#0a0026") }, // deep indigo
    uColorGlow: { value: new THREE.Color("#00f0ff") }, // cyan glow
    uIntensity: { value: 2.0 }
  }), []);

  useFrame((stateObj, delta) => {
    if (mesh.current) {
      const material = mesh.current.material as THREE.ShaderMaterial;
      material.uniforms.uTime.value += delta;
      
      // Target values based on state
      let targetAmplitude = 0.6; // Increased base idle amplitude
      let targetIntensity = 2.0;
      
      if (state === 'listening') {
        // Generation pulse: faster rotation, stronger distortion
        mesh.current.rotation.y += delta * 1.5;
        mesh.current.rotation.x += delta * 0.5;
        targetAmplitude = 1.0 + Math.sin(stateObj.clock.elapsedTime * 8) * 0.4;
        targetIntensity = 2.5;
      } else if (state === 'speaking') {
        // Playback distortion: reactive energy surges
        // NO rotational drift during speaking
        mesh.current.rotation.y += delta * 0.02;
        mesh.current.rotation.x += delta * 0.005;
        targetAmplitude =
          0.9 +
          Math.sin(stateObj.clock.elapsedTime * 10) * 0.25;
        targetIntensity = 2.0;
        material.uniforms.uColorGlow.value.lerp(
          new THREE.Color("#7a5cff"),
          0.025
        );
      } else {
        // Idle breathing - very cratery and alive, NO rotation so the patches stay where they are!
        targetAmplitude = 0.6 + Math.sin(stateObj.clock.elapsedTime * 1.5) * 0.15;
        targetIntensity = 1.8;
        material.uniforms.uColorGlow.value.lerp(new THREE.Color("#00f0ff"), 0.05); // cyan
      }
      
      // Smooth interpolation for amplitude and intensity
      material.uniforms.uAmplitude.value += (targetAmplitude - material.uniforms.uAmplitude.value) * 0.1;
      material.uniforms.uIntensity.value += (targetIntensity - material.uniforms.uIntensity.value) * 0.1;
    }
  });

  return (
    <Sphere ref={mesh} args={[2, 64, 64]}>
      <shaderMaterial
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        transparent={true}
      />
    </Sphere>
  );
}

export function Orb({ state = 'idle', className = "" }: { state?: 'idle' | 'listening' | 'speaking', className?: string }) {
  return (
    <div className={`relative w-[280px] h-[280px] md:w-[380px] md:h-[380px] ${className}`}>
      {/* Outer ambient glow */}
      <div 
        className="absolute inset-0 rounded-full blur-[100px] opacity-40 transition-all duration-1000"
        style={{
          background: state === 'speaking' ? 'radial-gradient(circle, #b53cff 0%, transparent 70%)' : 'radial-gradient(circle, #00f0ff 0%, transparent 70%)',
          transform: state !== 'idle' ? 'scale(1.2)' : 'scale(1)'
        }}
      />
      <Canvas camera={{ position: [0, 0, 5] }}>
        <ambientLight intensity={0.5} />
        <OrbMesh state={state} />
      </Canvas>
    </div>
  );
}
