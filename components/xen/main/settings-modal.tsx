"use client"

import { type ComponentType, useEffect, useMemo, useState } from "react"
import {
  ArrowUpRight,
  CircleDollarSign,
  LogOut,
  Mail,
  Moon,
  Shield,
  Sun,
  User,
  X,
} from "lucide-react"

type SettingsTabId = "profile" | "usage" | "general" | "community" | "feedback" | "terms"

type SettingsModalProps = {
  open: boolean
  onClose: () => void
}

type NavItem = {
  id: SettingsTabId
  label: string
  icon: ComponentType<{ className?: string }>
  external?: boolean
}

const navItems: NavItem[] = [
  { id: "profile", label: "Profile", icon: User },
  { id: "usage", label: "Usage", icon: CircleDollarSign },
  { id: "general", label: "General", icon: Sun },
  { id: "community", label: "Community", icon: Shield, external: true },
  { id: "feedback", label: "Feedback", icon: Mail, external: true },
  { id: "terms", label: "Terms & Policy", icon: Shield, external: true },
]

export default function SettingsModal({ open, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTabId>("profile")
  const [themeChoice, setThemeChoice] = useState<"system" | "light" | "dark">("light")

  useEffect(() => {
    if (!open) return

    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose()
    }

    window.addEventListener("keydown", onKeyDown)
    return () => {
      document.body.style.overflow = originalOverflow
      window.removeEventListener("keydown", onKeyDown)
    }
  }, [open, onClose])

  const content = useMemo(() => {
    if (activeTab === "profile") {
      return (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-xl bg-indigo-700" />
              <div>
                <h3 className="text-sm font-semibold text-zinc-100">John Doe</h3>
                <p className="text-[10px] text-zinc-400">Account Management</p>
              </div>
            </div>
            <button
              type="button"
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
              aria-label="Sign out"
            >
              <LogOut className="h-3 w-3" />
            </button>
          </div>

          <div className="rounded border border-zinc-700 bg-zinc-800 p-2">
            <p className="text-[10px] font-medium text-zinc-100">Password</p>
            <div className="mt-1 flex items-center justify-between gap-1.5">
              <p className="text-[10px] text-zinc-400">john@example.com</p>
              <button
                type="button"
                className="rounded border border-zinc-600 bg-zinc-700 px-2 py-0.5 text-[10px] text-zinc-100 hover:bg-zinc-600"
              >
                Set
              </button>
            </div>
          </div>
        </div>
      )
    }

    if (activeTab === "usage") {
      return (
        <div className="space-y-3">
          <section>
            <h3 className="text-sm font-semibold text-zinc-100">Plan</h3>
            <div className="mt-2 flex items-center justify-between rounded border border-zinc-700 bg-zinc-800 p-2">
              <div>
                <div className="flex items-center gap-1.5">
                  <CircleDollarSign className="h-3 w-3 text-zinc-300" />
                  <p className="text-base font-semibold text-zinc-100">300</p>
                  <span className="rounded bg-emerald-100 px-1 py-0.5 text-[9px] font-semibold text-emerald-700">
                    Free
                  </span>
                </div>
                <p className="text-[10px] text-zinc-400">Ends on 2026/12/31</p>
              </div>
              <button
                type="button"
                className="rounded bg-zinc-700 px-2 py-1 text-[10px] font-medium text-zinc-100 hover:bg-zinc-600"
              >
                Upgrade
              </button>
            </div>
          </section>

          <section>
            <h4 className="text-sm font-medium text-zinc-100">Credits Usage</h4>
            <div className="mt-2 overflow-hidden rounded border border-zinc-700">
              <table className="w-full border-collapse text-left text-[10px]">
                <thead className="bg-zinc-800 text-zinc-300">
                  <tr>
                    <th className="px-2 py-1 font-medium">Details</th>
                    <th className="px-2 py-1 font-medium">Type</th>
                    <th className="px-2 py-1 font-medium">Credits</th>
                    <th className="px-2 py-1 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-zinc-700 bg-zinc-800 text-zinc-300">
                    <td className="px-2 py-1">init</td>
                    <td className="px-2 py-1">Benefits Monthly</td>
                    <td className="px-2 py-1">300</td>
                    <td className="px-2 py-1">2026/02/27 10:54</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )
    }

    if (activeTab === "general") {
      const modes: Array<{ id: "system" | "light" | "dark"; label: string; icon: ComponentType<{ className?: string }> }> = [
        { id: "system", label: "System Mode", icon: Shield },
        { id: "light", label: "Light Mode", icon: Sun },
        { id: "dark", label: "Dark Mode", icon: Moon },
      ]

      return (
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">Theme</h3>
          <div className="mt-2 grid grid-cols-1 gap-1.5 md:grid-cols-3">
            {modes.map((mode) => {
              const Icon = mode.icon
              const isActive = themeChoice === mode.id
              return (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => setThemeChoice(mode.id)}
                  className={`rounded border p-3 text-center transition-colors ${
                    isActive
                      ? "border-zinc-600 bg-zinc-800 text-zinc-100"
                      : "border-zinc-700 bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                  }`}
                >
                  <Icon className="mx-auto mb-1 h-4 w-4" />
                  <span className="text-xs font-medium">{mode.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      )
    }

    const label = navItems.find((item) => item.id === activeTab)?.label || "Section"
    return (
      <div className="rounded border border-zinc-700 bg-zinc-800 p-3">
        <p className="text-xs text-zinc-300">{label} links can be connected here.</p>
      </div>
    )
  }, [activeTab, themeChoice])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[100]">
      <button
        type="button"
        aria-label="Close settings"
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <section className="relative h-[50vh] w-full max-w-xl overflow-hidden rounded-lg bg-zinc-900 shadow-xl">
          <header className="flex items-center justify-between px-4 pb-1 pt-2">
            <h2 className="text-lg font-semibold text-zinc-100">Setting</h2>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-2 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </header>

          <div className="grid h-[calc(50vh-36px)] grid-cols-1 md:grid-cols-[150px_1fr]">
            <aside className="px-2 py-1 md:px-3">
              <nav className="space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const selected = activeTab === item.id
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setActiveTab(item.id)}
                      className={`flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-left text-xs transition-colors ${
                        selected ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:bg-zinc-800"
                      }`}
                    >
                      <Icon className="h-3 w-3" />
                      <span className="flex-1">{item.label}</span>
                      {item.external && <ArrowUpRight className="h-2.5 w-2.5 text-zinc-500" />}
                    </button>
                  )
                })}
              </nav>
            </aside>

            <main className="overflow-y-auto px-3 py-2 md:px-4 md:py-3 bg-zinc-900">{content}</main>
          </div>
        </section>
      </div>
    </div>
  )
}
