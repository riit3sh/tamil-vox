"use client";

import React, { useState } from 'react';
import { Mic, Send, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceConsoleProps {
  onSubmit: (prompt: string) => void;
  isProcessing: boolean;
}

export function VoiceConsole({ onSubmit, isProcessing }: VoiceConsoleProps) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isProcessing) {
      onSubmit(prompt);
      setPrompt('');
    }
  };

  return (
    <div className="fixed bottom-10 left-1/2 -translate-x-1/2 w-[90%] max-w-lg z-50">
      <motion.form 
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.8, ease: "easeOut" }}
        onSubmit={handleSubmit}
        className="glass-panel p-2 pl-6 pr-2 flex items-center gap-4"
      >
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Say something in Tanglish..."
          className="flex-1 bg-transparent border-none outline-none text-white/90 placeholder:text-white/40 text-lg font-light tracking-wide"
          disabled={isProcessing}
        />
        
        <div className="flex items-center gap-2">
          <button 
            type="submit"
            className="glass-button w-12 h-12 text-white bg-white/10"
            disabled={!prompt.trim() || isProcessing}
          >
            <AnimatePresence mode="wait">
              {isProcessing ? (
                <motion.div
                  key="loader"
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  exit={{ opacity: 0, rotate: 90 }}
                  className="animate-spin"
                >
                  <Loader2 className="w-5 h-5" />
                </motion.div>
              ) : (
                <motion.div
                  key="send"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                >
                  <Send className="w-5 h-5 ml-[-2px]" />
                </motion.div>
              )}
            </AnimatePresence>
          </button>
        </div>
      </motion.form>
    </div>
  );
}
