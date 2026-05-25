"use client";

import { motion } from 'framer-motion';

export function PipelineAnimation() {
  const steps = ["Tanglish", "Renderer", "Phonetic Tamil", "TTS"];

  return (
    <div className="flex items-center justify-center gap-3 mt-4 text-xs font-mono text-white/40 uppercase tracking-widest">
      {steps.map((step, idx) => (
        <div key={step} className="flex items-center gap-3">
          <motion.span
            initial={{ opacity: 0.3 }}
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: idx * 0.5,
              ease: "easeInOut"
            }}
          >
            {step}
          </motion.span>
          {idx < steps.length - 1 && (
            <span className="text-white/20">→</span>
          )}
        </div>
      ))}
    </div>
  );
}
