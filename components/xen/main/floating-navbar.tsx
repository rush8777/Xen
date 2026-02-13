"use client";
import React, { useState } from "react";
import {
  motion,
  AnimatePresence,
  useScroll,
  useMotionValueEvent,
} from "motion/react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

export const FloatingNav = ({
  navItems,
  className,
}: {
  navItems: {
    name: string;
    link: string;
    icon?: JSX.Element;
    hasDropdown?: boolean;
  }[];
  className?: string;
}) => {
  const { scrollYProgress } = useScroll();
  const [visible, setVisible] = useState(false);

  useMotionValueEvent(scrollYProgress, "change", (current) => {
    if (typeof current === "number") {
      let direction = current! - scrollYProgress.getPrevious()!;

      if (scrollYProgress.get() < 0.05) {
        setVisible(false);
      } else {
        if (direction < 0) {
          setVisible(true);
        } else {
          setVisible(false);
        }
      }
    }
  });

  return (
    <AnimatePresence mode="wait">
      <motion.div
        initial={{
          opacity: 1,
          y: -100,
        }}
        animate={{
          y: visible ? 0 : -100,
          opacity: visible ? 1 : 0,
        }}
        transition={{
          duration: 0.2,
        }}
        className={cn(
          "flex fixed top-6 inset-x-0 mx-auto border border-white/[0.1] rounded-full bg-black/80 backdrop-blur-lg shadow-lg z-[5000] px-8 py-3 items-center justify-between max-w-6xl",
          className
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-6 h-6">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="3" fill="#8B5CF6" />
              <circle cx="16" cy="8" r="3" fill="#8B5CF6" opacity="0.6" />
              <circle cx="8" cy="16" r="3" fill="#8B5CF6" opacity="0.6" />
              <circle cx="16" cy="16" r="3" fill="#8B5CF6" opacity="0.4" />
            </svg>
          </div>
          <span className="text-lg font-semibold text-white">
            Apex<sup className="text-xs">™</sup>
          </span>
        </div>

        {/* Nav Items */}
        <div className="hidden md:flex items-center gap-8">
          {navItems.map((navItem: any, idx: number) => (
            <a
              key={`link=${idx}`}
              href={navItem.link}
              className="text-sm text-gray-300 hover:text-white transition-colors flex items-center gap-1"
            >
              {navItem.name}
              {navItem.hasDropdown && <ChevronDown className="h-4 w-4" />}
            </a>
          ))}
        </div>

        {/* CTA Button */}
        <button className="rounded-full border border-violet-500 text-violet-400 hover:bg-violet-500/10 hover:text-violet-300 bg-transparent px-4 py-2 text-sm font-medium transition-colors">
          Request a demo
        </button>
      </motion.div>
    </AnimatePresence>
  );
};