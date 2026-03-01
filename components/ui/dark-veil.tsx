"use client"
import { useEffect, useRef } from 'react'

interface DarkVeilProps {
  hueShift?: number
  noiseIntensity?: number
  scanlineIntensity?: number
  warpAmount?: number
  scanlineFrequency?: number
  speed?: number
  className?: string
}

export const DarkVeil = ({
  hueShift = 0,
  noiseIntensity = 0.1,
  scanlineIntensity = 0.05,
  warpAmount = 0.02,
  scanlineFrequency = 4.0,
  speed = 1,
  className = ""
}: DarkVeilProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number | null>(null)
  const timeRef = useRef(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl') as WebGLRenderingContext
    if (!gl) return

    // Vertex shader
    const vertexShaderSource = `
      attribute vec2 position;
      varying vec2 vUv;
      void main() {
        vUv = position * 0.5 + 0.5;
        gl_Position = vec4(position, 0.0, 1.0);
      }
    `

    // Fragment shader with dark veil effect
    const fragmentShaderSource = `
      precision mediump float;
      varying vec2 vUv;
      uniform float time;
      uniform float hueShift;
      uniform float noiseIntensity;
      uniform float scanlineIntensity;
      uniform float warpAmount;
      uniform float scanlineFrequency;

      // Noise function
      float random(vec2 st) {
        return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
      }

      float noise(vec2 st) {
        vec2 i = floor(st);
        vec2 f = fract(st);
        float a = random(i);
        float b = random(i + vec2(1.0, 0.0));
        float c = random(i + vec2(0.0, 1.0));
        float d = random(i + vec2(1.0, 1.0));
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
      }

      // HSV to RGB conversion
      vec3 hsv2rgb(vec3 c) {
        vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
        vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
        return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
      }

      void main() {
        vec2 uv = vUv;
        
        // Warp effect
        uv.x += sin(uv.y * 10.0 + time * 2.0) * warpAmount;
        uv.y += cos(uv.x * 8.0 + time * 1.5) * warpAmount;
        
        // Noise
        float n = noise(uv * 20.0 + time * 0.5) * noiseIntensity;
        
        // Scanlines
        float scanlines = sin(uv.y * scanlineFrequency * 3.14159) * scanlineIntensity;

        // Purple veil base + animated purple highlights
        float wave = 0.5 + 0.5 * sin((uv.x * 3.0 + uv.y * 2.0) * 3.14159 + time * 1.4);
        vec3 base = vec3(0.03, 0.01, 0.06);
        vec3 purple = vec3(0.45, 0.12, 0.70);
        vec3 color = mix(base, purple, wave * 0.35);
        color *= (0.85 + n * 0.8);
        
        // Apply effects
        color += scanlines;
        color += n;
        
        gl_FragColor = vec4(color, 1.0);
      }
    `

    // Compile shaders
    const compileShader = (source: string, type: number) => {
      const shader = gl.createShader(type)
      if (!shader) return null
      gl.shaderSource(shader, source)
      gl.compileShader(shader)
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compilation error:', gl.getShaderInfoLog(shader))
        gl.deleteShader(shader)
        return null
      }
      return shader
    }

    const vertexShader = compileShader(vertexShaderSource, gl.VERTEX_SHADER)
    const fragmentShader = compileShader(fragmentShaderSource, gl.FRAGMENT_SHADER)

    if (!vertexShader || !fragmentShader) return

    // Create program
    const program = gl.createProgram()
    if (!program) return

    gl.attachShader(program, vertexShader)
    gl.attachShader(program, fragmentShader)
    gl.linkProgram(program)

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Program linking error:', gl.getProgramInfoLog(program))
      return
    }

    // Set up geometry
    const vertices = new Float32Array([
      -1, -1,
       1, -1,
      -1,  1,
       1,  1,
    ])

    const buffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW)

    const positionLocation = gl.getAttribLocation(program, 'position')
    gl.enableVertexAttribArray(positionLocation)
    gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0)

    // Get uniform locations
    const timeLocation = gl.getUniformLocation(program, 'time')
    const hueShiftLocation = gl.getUniformLocation(program, 'hueShift')
    const noiseIntensityLocation = gl.getUniformLocation(program, 'noiseIntensity')
    const scanlineIntensityLocation = gl.getUniformLocation(program, 'scanlineIntensity')
    const warpAmountLocation = gl.getUniformLocation(program, 'warpAmount')
    const scanlineFrequencyLocation = gl.getUniformLocation(program, 'scanlineFrequency')

    // Resize canvas
    const resizeCanvas = () => {
      canvas.width = canvas.clientWidth
      canvas.height = canvas.clientHeight
      gl.viewport(0, 0, canvas.width, canvas.height)
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Animation loop
    const animate = () => {
      timeRef.current += 0.01 * speed
      
      gl.useProgram(program)
      gl.uniform1f(timeLocation, timeRef.current)
      gl.uniform1f(hueShiftLocation, hueShift)
      gl.uniform1f(noiseIntensityLocation, noiseIntensity)
      gl.uniform1f(scanlineIntensityLocation, scanlineIntensity)
      gl.uniform1f(warpAmountLocation, warpAmount)
      gl.uniform1f(scanlineFrequencyLocation, scanlineFrequency)
      
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
      
      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      gl.deleteProgram(program)
      gl.deleteShader(vertexShader)
      gl.deleteShader(fragmentShader)
      gl.deleteBuffer(buffer)
    }
  }, [hueShift, noiseIntensity, scanlineIntensity, warpAmount, scanlineFrequency, speed])

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full ${className}`}
      style={{ opacity: 0.75 }} // Increased opacity to 75% for more visible background effect
    />
  )
}
