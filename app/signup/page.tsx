"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"

// ─── Shared assets ────────────────────────────────────────────────────────────

const SPACE_BG =
  "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1400&q=80&auto=format&fit=crop"

function GalaxyPanel() {
  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* galaxy image */}
      <img
        src={SPACE_BG}
        alt="galaxy"
        className="absolute inset-0 w-full h-full object-cover object-center"
      />

      {/* thin crosshair lines */}
      <div className="absolute inset-0 pointer-events-none">
        {/* vertical center line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/20" />
        {/* horizontal center line */}
        <div className="absolute top-1/2 left-0 right-0 h-px bg-white/20" />
      </div>

      {/* arched border — top-half arch clipped */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "transparent",
          boxShadow: "inset 0 0 80px 20px rgba(0,0,0,0.55)",
        }}
      />

      {/* arch shape overlay (top semicircle border) */}
      <div
        className="absolute pointer-events-none"
        style={{
          top: "5%",
          left: "50%",
          transform: "translateX(-50%)",
          width: "80%",
          aspectRatio: "1",
          borderRadius: "50% 50% 0 0",
          border: "1px solid rgba(255,255,255,0.18)",
          borderBottom: "none",
        }}
      />

      {/* dotted arc sweep */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox="0 0 600 600"
        preserveAspectRatio="xMidYMid meet"
      >
        <path
          d="M 550 580 A 380 380 0 0 0 50 200"
          fill="none"
          stroke="rgba(255,255,255,0.25)"
          strokeWidth="0.8"
          strokeDasharray="4 6"
        />
      </svg>

      {/* scan-box telemetry HUD */}
      <div
        className="absolute pointer-events-none"
        style={{ bottom: "30%", right: "30%", transform: "translate(50%,50%)" }}
      >
        <div
          className="w-12 h-12 border border-white/40"
          style={{ boxShadow: "0 0 12px rgba(255,255,255,0.1)" }}
        />
      </div>
      <div
        className="absolute font-mono text-[9px] leading-tight text-green-300/70 pointer-events-none"
        style={{ bottom: "26%", right: "22%" }}
      >
        <div>satellite: tango-razor01</div>
        <div>status: 200%</div>
        <div>group: -13</div>
      </div>

      {/* bottom-left texture grid (isometric dot pattern) */}
      <div
        className="absolute bottom-0 left-0 w-full h-48 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px)",
          backgroundSize: "18px 18px",
          maskImage: "linear-gradient(to top, rgba(0,0,0,0.4) 0%, transparent 100%)",
          WebkitMaskImage:
            "linear-gradient(to top, rgba(0,0,0,0.4) 0%, transparent 100%)",
        }}
      />
    </div>
  )
}

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <div className="w-5 h-5 rounded-full bg-zinc-700 border border-zinc-600 flex items-center justify-center">
        <div className="w-2 h-2 rounded-full bg-zinc-400" />
      </div>
      <span className="text-sm font-medium text-zinc-300 tracking-wide">Orion</span>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path
        d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
        fill="#4285F4"
      />
      <path
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z"
        fill="#34A853"
      />
      <path
        d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
        fill="#FBBC05"
      />
      <path
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z"
        fill="#EA4335"
      />
    </svg>
  )
}

// ─── Input ────────────────────────────────────────────────────────────────────

function AuthInput({ label, type = "text", placeholder, value, onChange }: {
  label: string;
  type?: string;
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-[11px] text-zinc-400 tracking-wide">{label}</label>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={cn(
          "w-full px-3 py-2.5 rounded-md text-sm",
          "bg-zinc-800/80 border border-zinc-700",
          "text-zinc-100 placeholder:text-zinc-500",
          "outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-600",
          "transition-all duration-150"
        )}
      />
    </div>
  )
}

// ─── Buttons ─────────────────────────────────────────────────────────────────

function PrimaryButton({ children, onClick, type = "button" }: {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={cn(
        "w-full py-2.5 rounded-md text-sm font-medium",
        "bg-[#8db88a] hover:bg-[#9dc99a] active:bg-[#7da87a]",
        "text-zinc-900 transition-colors duration-150",
        "tracking-wide"
      )}
    >
      {children}
    </button>
  )
}

function GoogleButton({ onClick }: {
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full py-2.5 rounded-md text-sm font-medium",
        "bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-800",
        "border border-zinc-700 hover:border-zinc-600",
        "text-zinc-200 transition-colors duration-150",
        "flex items-center justify-center gap-2.5"
      )}
    >
      <GoogleIcon />
      <span>Continue with Google</span>
    </button>
  )
}

// ─── Divider ─────────────────────────────────────────────────────────────────

function Divider() {
  return (
    <div className="relative flex items-center gap-3">
      <div className="flex-1 h-px bg-zinc-800" />
      <span className="text-[10px] text-zinc-600 uppercase tracking-widest">or</span>
      <div className="flex-1 h-px bg-zinc-800" />
    </div>
  )
}

// ─── Signup Page ──────────────────────────────────────────────────────────────

export default function SignupPage() {
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [password, setPassword] = useState("")

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center"
      style={{ background: "#111110" }}
    >
      <div
        className="w-full max-w-5xl mx-4 rounded-2xl overflow-hidden grid grid-cols-1 md:grid-cols-2"
        style={{
          background: "#161614",
          border: "1px solid rgba(255,255,255,0.07)",
          minHeight: 560,
        }}
      >
        {/* ── Left: Form ── */}
        <div className="flex flex-col justify-between p-10 md:p-12 relative">
          {/* dot-grid texture */}
          <div
            className="absolute bottom-0 left-0 w-full h-52 pointer-events-none rounded-bl-2xl"
            style={{
              backgroundImage:
                "radial-gradient(circle, rgba(255,255,255,0.045) 1px, transparent 1px)",
              backgroundSize: "16px 16px",
              maskImage: "linear-gradient(to top, black 0%, transparent 80%)",
              WebkitMaskImage: "linear-gradient(to top, black 0%, transparent 80%)",
            }}
          />

          <div className="relative z-10 space-y-8">
            <Logo />

            <div>
              <h1
                className="text-3xl font-bold text-white leading-tight"
                style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
              >
                Start watching the<br />
                darkness with us
              </h1>
              <p className="mt-2 text-sm text-zinc-500">
                Create your account in seconds.
              </p>
            </div>

            <div className="space-y-4">
              <GoogleButton onClick={() => {}} />

              <Divider />

              <AuthInput
                label="Full name"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
              />

              <AuthInput
                label="Email"
                type="email"
                placeholder="Your email"
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              />

              <AuthInput
                label="Password"
                type="password"
                placeholder="Create a password"
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              />

              <PrimaryButton onClick={() => {}}>Continue with email</PrimaryButton>

              <p className="text-center text-[10px] text-zinc-600 leading-relaxed">
                By signing up, you agree to our{" "}
                <a href="#" className="text-zinc-400 underline underline-offset-2 hover:text-zinc-300">
                  Terms and Conditions
                </a>{" "}
                and{" "}
                <a href="#" className="text-zinc-400 underline underline-offset-2 hover:text-zinc-300">
                  Privacy Policy
                </a>
                .
              </p>
            </div>
          </div>

          {/* Bottom link */}
          <div className="relative z-10 mt-6">
            <div
              className={cn(
                "inline-flex items-center gap-3 px-4 py-2.5 rounded-lg",
                "border border-zinc-800 bg-zinc-900/60"
              )}
            >
              <span className="text-xs text-zinc-400">Already have an account?</span>
              <button
                onClick={() => window.location.href = '/login'}
                className="text-xs font-medium text-white bg-zinc-800 hover:bg-zinc-700 px-3 py-1 rounded-md transition-colors"
              >
                Log in
              </button>
            </div>
          </div>
        </div>

        {/* ── Right: Galaxy ── */}
        <div className="hidden md:block relative">
          <GalaxyPanel />
        </div>
      </div>
    </div>
  )
}
