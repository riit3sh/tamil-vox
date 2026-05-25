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
  vNormal = normal;
  
  // Create noise based displacement
  float noise = snoise(vec3(position.x * 2.0, position.y * 2.0 + uTime * 0.5, position.z * 2.0));
  
  // Apply amplitude multiplier for voice reaction
  vec3 newPosition = position + normal * (noise * uAmplitude * 0.2);
  vPosition = newPosition;
  
  gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
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
  // Edge glow effect (Fresnel)
  vec3 viewDirection = normalize(cameraPosition - vPosition);
  float fresnel = dot(viewDirection, vNormal);
  fresnel = clamp(1.0 - fresnel, 0.0, 1.0);
  fresnel = pow(fresnel, 2.5); // sharper edge
  
  // Layered volumetric noise
  float noise1 = snoise(vec3(vPosition.x * 1.5, vPosition.y * 1.5 + uTime * 0.4, vPosition.z * 1.5));
  float noise2 = snoise(vec3(vPosition.x * 3.0 - uTime * 0.2, vPosition.y * 3.0, vPosition.z * 3.0 + uTime * 0.3));
  float layeredNoise = (noise1 * 0.7) + (noise2 * 0.3);
  
  // Map noise to colors
  float pulse = sin(uTime * 1.5) * 0.5 + 0.5;
  
  // Inner dark core with glowing plasma streaks
  vec3 innerPlasma = mix(uColorBase, uColorGlow, smoothstep(-0.2, 0.8, layeredNoise + pulse * 0.2));
  
  // Add volumetric opacity falloff at edges
  float alpha = smoothstep(0.0, 0.4, fresnel) + 0.6;
  
  // Final mix with fresnel edge glow
  vec3 finalColor = mix(innerPlasma, uColorGlow, fresnel * uIntensity);
  
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
      mesh.current.rotation.y += delta * 0.1;
      mesh.current.rotation.x += delta * 0.05;
      
      const material = mesh.current.material as THREE.ShaderMaterial;
      material.uniforms.uTime.value += delta;
      
      // Target values based on state
      let targetAmplitude = 0.2;
      let targetIntensity = 2.0;
      
      if (state === 'listening') {
        // Generation pulse: faster rotation, stronger distortion
        mesh.current.rotation.y += delta * 0.5;
        targetAmplitude = 0.5 + Math.sin(stateObj.clock.elapsedTime * 8) * 0.3;
        targetIntensity = 2.5;
      } else if (state === 'speaking') {
        // Playback distortion: reactive energy surges
        mesh.current.rotation.y += delta * 0.2;
        targetAmplitude = 0.6 + Math.sin(stateObj.clock.elapsedTime * 15) * 0.5;
        targetIntensity = 3.5;
        material.uniforms.uColorGlow.value.lerp(new THREE.Color("#b53cff"), 0.08); // violet/pink
      } else {
        // Idle breathing
        targetAmplitude = 0.2 + Math.sin(stateObj.clock.elapsedTime * 2) * 0.05;
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
    <div className={`relative w-[300px] h-[300px] md:w-[500px] md:h-[500px] ${className}`}>
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
