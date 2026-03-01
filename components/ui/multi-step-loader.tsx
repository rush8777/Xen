"use client";
import { cn } from "@/lib/utils";
import { useEffect, useMemo, useState } from "react";
import { ShinyText } from "@/components/ui/shiny-text";

type LoadingState = {
  text: string;
};

type MultiStepLoaderProps = {
  loadingStates: LoadingState[];
  loading?: boolean;
  duration?: number;
  loop?: boolean;
  value?: number;
  overlay?: "fixed" | "absolute";
};

export const MultiStepLoader = ({
  loadingStates,
  loading,
  duration = 2000,
  loop = true,
  value,
  overlay,
}: MultiStepLoaderProps) => {
  const [currentState, setCurrentState] = useState(0);

  const safeStates = useMemo(
    () => (loadingStates.length > 0 ? loadingStates : [{ text: "Initializing" }]),
    [loadingStates]
  );

  useEffect(() => {
    if (!loading) {
      setCurrentState(0);
      return;
    }
    if (typeof value === "number") return;

    const interval = setInterval(() => {
      setCurrentState((prev) =>
        loop ? (prev + 1) % safeStates.length : Math.min(prev + 1, safeStates.length - 1)
      );
    }, duration);

    return () => clearInterval(interval);
  }, [loading, value, loop, duration, safeStates.length]);

  if (!loading) return null;

  const safeIndex = Math.min(
    Math.max(typeof value === "number" ? value : currentState, 0),
    safeStates.length - 1
  );
  const currentText = safeStates[safeIndex]?.text ?? "Initializing";

  return (
    <div
      className={cn(
        "w-full h-full inset-0 z-[100] flex flex-col items-center justify-center gap-5 overflow-hidden bg-black",
        (overlay || "fixed") === "absolute" ? "absolute" : "fixed"
      )}
    >
      <video
        className="w-[460px] max-w-[85vw] max-h-[65vh] object-contain bg-black"
        src="/animation/loading_screen.mp4"
        autoPlay
        loop
        muted
        playsInline
      />
      <ShinyText
        text={currentText}
        className="text-sm sm:text-base font-medium tracking-wide"
        duration={2.2}
        shineWidth={3}
      />
    </div>
  );
};
