"use client"

import { useEffect } from "react"

export function ScrollbarVisibilityManager() {
  useEffect(() => {
    const timers = new WeakMap<Element, ReturnType<typeof setTimeout>>()

    const isScrollable = (el: Element) => {
      const style = window.getComputedStyle(el)
      const overflowY = style.overflowY
      const overflowX = style.overflowX
      const canScrollY = (overflowY === "auto" || overflowY === "scroll") && el.scrollHeight > el.clientHeight
      const canScrollX = (overflowX === "auto" || overflowX === "scroll") && el.scrollWidth > el.clientWidth
      return canScrollY || canScrollX
    }

    const findScrollableAncestor = (start: EventTarget | null): Element => {
      if (!(start instanceof Element)) return document.documentElement
      let current: Element | null = start
      while (current && current !== document.documentElement) {
        if (isScrollable(current)) return current
        current = current.parentElement
      }
      return document.documentElement
    }

    const markScrolling = (el: Element) => {
      el.classList.add("is-scrolling-now")
      const existing = timers.get(el)
      if (existing) clearTimeout(existing)
      const timer = setTimeout(() => {
        el.classList.remove("is-scrolling-now")
        timers.delete(el)
      }, 700)
      timers.set(el, timer)
    }

    const onScroll = (event: Event) => {
      const target = event.target === document ? document.documentElement : (event.target as EventTarget | null)
      markScrolling(findScrollableAncestor(target))
    }

    const onPointerScrollIntent = (event: Event) => {
      markScrolling(findScrollableAncestor(event.target))
    }

    document.addEventListener("scroll", onScroll, true)
    window.addEventListener("wheel", onPointerScrollIntent, { passive: true })
    window.addEventListener("touchmove", onPointerScrollIntent, { passive: true })

    return () => {
      document.removeEventListener("scroll", onScroll, true)
      window.removeEventListener("wheel", onPointerScrollIntent)
      window.removeEventListener("touchmove", onPointerScrollIntent)
      document.querySelectorAll(".is-scrolling-now").forEach((el) => {
        el.classList.remove("is-scrolling-now")
      })
    }
  }, [])

  return null
}
