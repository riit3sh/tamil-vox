"use client";

import React from "react";
import { motion } from "framer-motion";

export function VaporHeading({ text }: { text: string }) {
  // We split the text into words to give a subtle staggered vapor effect
  const words = text.split(" ");

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2,
      },
    },
  };

  const item = {
    hidden: { 
      opacity: 0, 
      filter: "blur(10px)", 
      y: 10, 
      scale: 0.98 
    },
    show: { 
      opacity: 1, 
      filter: "blur(0px)", 
      y: 0, 
      scale: 1,
      transition: {
        duration: 1.5,
        ease: [0.16, 1, 0.3, 1], 
      }
    },
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="relative w-full flex justify-center items-center"
    >
      <h1 
        className="text-white/90 font-light tracking-tight text-center flex flex-nowrap justify-center gap-x-[0.25em] whitespace-nowrap"
        style={{ 
          fontSize: "clamp(32px, 4vw, 64px)", // Scaled down from the user's 84px max to ensure it doesn't wrap and looks elegant
          fontWeight: 300,
          lineHeight: 1.05,
          textShadow: "0 0 20px rgba(255,255,255,0.1)"
        }}
      >
        {words.map((word, i) => (
          <motion.span key={i} variants={item} className="inline-block">
            {word}
          </motion.span>
        ))}
      </h1>
    </motion.div>
  );
}
