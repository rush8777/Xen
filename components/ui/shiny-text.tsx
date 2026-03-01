"use client";

import { cn } from "@/lib/utils";
import { motion } from "motion/react";

export function ShinyText({
  text,
  className,
  shineWidth = 40,
  duration = 2.2,
}: {
  text: string;
  className?: string;
  shineWidth?: number;
  duration?: number;
}) {
  return (
    <motion.span
      className={cn(
        "relative inline-block bg-[linear-gradient(110deg,rgba(255,255,255,0.18),rgba(255,255,255,0.18),rgba(255,255,255,0.95),rgba(255,255,255,0.18),rgba(255,255,255,0.18))] bg-[length:200%_100%] bg-clip-text text-transparent",
        className
      )}
      animate={{ backgroundPositionX: ["0%", "-200%"] }}
      transition={{ duration, repeat: Infinity, ease: "linear" }}
      style={{
        WebkitTextFillColor: "transparent",
        maskImage: `linear-gradient(90deg, transparent 0%, black ${shineWidth}%, black ${100 - shineWidth}%, transparent 100%)`,
        WebkitMaskImage: `linear-gradient(90deg, transparent 0%, black ${shineWidth}%, black ${100 - shineWidth}%, transparent 100%)`,
      }}
    >
      {text}
    </motion.span>
  );
}
