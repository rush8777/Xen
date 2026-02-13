"use client";
import React from "react";
import { FloatingNav } from "@/components/ui/floating-navbar";

export default function FloatingNavDemo() {
  const navItems = [
    {
      name: "Products",
      link: "#products",
    },
    {
      name: "Solutions",
      link: "#solutions",
      hasDropdown: true,
    },
    {
      name: "Resources",
      link: "#resources",
    },
    {
      name: "Pricing",
      link: "#pricing",
    },
    {
      name: "Contact",
      link: "#contact",
    },
  ];

  return (
    <div className="relative w-full">
      <FloatingNav navItems={navItems} />
      <DummyContent />
    </div>
  );
}

const DummyContent = () => {
  return (
    <div className="grid grid-cols-1 h-[40rem] w-full bg-black relative border border-white/[0.1] rounded-md">
      <p className="text-white text-center text-4xl mt-40 font-bold">
        Scroll down and back up to reveal Navbar
      </p>
      <div className="inset-0 absolute bg-grid-white/[0.05]" />
    </div>
  );
};