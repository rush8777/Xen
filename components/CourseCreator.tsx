"use client";

import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import WelcomeCard from "./cards/WelcomeCard";
import PurposeCard from "./cards/PurposeCard";
import RoleCard from "./cards/RoleCard";
import GoalsCard from "./cards/GoalsCard";
import TopicCard from "./cards/TopicCard";
import GeneratingCard from "./cards/GeneratingCard";
import OutlineCard from "./cards/OutlineCard";
import FinalCard from "./cards/FinalCard";

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 600 : -600,
    opacity: 0,
    scale: 0.95,
  }),
  center: {
    x: 0,
    opacity: 1,
    scale: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 600 : -600,
    opacity: 0,
    scale: 0.95,
  }),
};

export interface CourseData {
  topic: string;
  outline: string[];
  description: string;
}

interface CourseCreatorProps {
  onComplete?: () => void;
  variant?: "page" | "overlay";
}

const CourseCreator = ({ onComplete, variant = "page" }: CourseCreatorProps) => {
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [courseData, setCourseData] = useState<CourseData>({
    topic: "",
    outline: [],
    description: "",
  });

  // Lock body scroll when overlay is active
  useEffect(() => {
    if (variant === "overlay") {
      // Save original styles
      const originalStyle = window.getComputedStyle(document.body);
      const originalOverflow = originalStyle.overflow;
      
      // Lock scroll
      document.body.style.overflow = 'hidden';
      
      // Cleanup function to restore scroll
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [variant]);

  const goNext = () => {
    setDirection(1);
    setStep((s) => s + 1);
  };

  const goBack = () => {
    setDirection(-1);
    setStep((s) => s - 1);
  };

  const handleTopicSubmit = (topic: string) => {
    setCourseData((prev) => ({ ...prev, topic }));
    goNext();
    // Simulate AI generation
    setTimeout(() => {
      setCourseData((prev) => ({
        ...prev,
        description: `A comprehensive course covering the fundamentals and advanced concepts of ${topic}. Designed for learners who want to master this subject through practical examples and real-world applications.`,
        outline: [
          "Introduction & Core Concepts",
          "Fundamentals Deep Dive",
          "Practical Applications",
          "Advanced Techniques",
          "Case Studies & Projects",
          "Assessment & Certification",
        ],
      }));
      setDirection(1);
      setStep(6);
    }, 3000);
  };

  const handleRestart = () => {
    setDirection(-1);
    setStep(0);
    setCourseData({ topic: "", outline: [], description: "" });
  };

  const cards = [
    <WelcomeCard key="welcome" onStart={goNext} />,
    <PurposeCard key="purpose" onSelect={() => goNext()} onBack={goBack} />,
    <RoleCard key="role" onSelect={() => goNext()} onBack={goBack} />,
    <GoalsCard key="goals" onSubmit={() => goNext()} onBack={goBack} />,
    <TopicCard key="topic" onSubmit={handleTopicSubmit} onBack={goBack} />,
    <GeneratingCard key="generating" topic={courseData.topic} />,
    <OutlineCard key="outline" courseData={courseData} onNext={goNext} onBack={() => { setDirection(-1); setStep(4); }} />,
    <FinalCard key="final" courseData={courseData} onRestart={handleRestart} onComplete={onComplete} />,
  ];

  return (
    <div
      className={
        variant === "overlay"
          ? "relative w-full flex items-center justify-center p-4 overflow-hidden rounded-2xl"
          : "flex min-h-screen items-center justify-center p-4 overflow-hidden"
      }
    >
      {/* Subtle background pattern */}
      <div
        className={variant === "overlay" ? "absolute inset-0 opacity-[0.02]" : "fixed inset-0 opacity-[0.02]"}
        style={{
          backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative w-full max-w-5xl" style={{ minHeight: "560px" }}>
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={step}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ 
              type: "spring", 
              stiffness: 260, 
              damping: 25,
              mass: 0.8
            }}
            className="absolute inset-0 flex items-center justify-center"
          >
            {cards[step]}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Step indicator */}
      <div
        className={
          variant === "overlay"
            ? "absolute -bottom-12 left-1/2 -translate-x-1/2 flex gap-2"
            : "fixed bottom-8 left-1/2 -translate-x-1/2 flex gap-2"
        }
      >
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div
            key={i}
            className={`h-2 rounded-full transition-all duration-500 ${
              i === step 
                ? "w-8 bg-purple-500" 
                : "w-2 bg-zinc-700"
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default CourseCreator;
