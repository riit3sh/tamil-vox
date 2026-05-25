"use client";

import React, { useState } from 'react';
import { Orb } from '@/components/Orb';
import { VoiceConsole } from '@/components/VoiceConsole';
import { PipelineAnimation } from '@/components/PipelineAnimation';
import { DemoSection } from '@/components/DemoSection';
import { Github } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { VaporHeading } from '@/components/ui/vapor-heading';

export default function Home() {
  const [orbState, setOrbState] = useState<'idle' | 'listening' | 'speaking'>('idle');
  const [subtitleText, setSubtitleText] = useState<string>('');

  const handlePromptSubmit = async (prompt: string) => {
    setOrbState('listening');
    setSubtitleText('');
    
    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: prompt })
      });
      
      const data = await response.json();
      
      if (data.audio_base64) {
        setSubtitleText(data.display_text || '');
        const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
        audio.onended = () => {
          setOrbState('idle');
          setSubtitleText('');
        };
        audio.play().catch(e => {
          console.error("Audio playback failed:", e);
          setOrbState('idle');
          setSubtitleText('');
        });
        setOrbState('speaking');
      } else {
        setOrbState('idle');
        setSubtitleText('');
      }
    } catch (error) {
      console.error("Failed to fetch from backend:", error);
      setOrbState('idle');
    }
  };

  return (
    <main className="min-h-screen bg-black overflow-hidden flex flex-col relative selection:bg-indigo-500/30">
      
      {/* ── AMBIENT BACKGROUND ── */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(50,10,120,0.15)_0%,rgba(0,0,0,1)_70%)]" />
        <div className="absolute inset-0 bg-black/40 backdrop-blur-[100px]" />
      </div>
      
      {/* ── TOP NAV ── */}
      <header className="w-full flex items-center justify-between p-6 absolute top-0 z-50">
        <div className="font-mono text-sm tracking-[0.2em] uppercase text-white/50">
          Tamilvox
        </div>
        <a 
          href="https://github.com/riit3sh/tamil-vox" 
          target="_blank" 
          rel="noreferrer"
          className="glass-button w-10 h-10 bg-white/5 hover:bg-white/10"
        >
          <Github className="w-4 h-4 text-white/70" />
        </a>
      </header>

      {/* ── HERO SECTION ── */}
      <section className="relative w-full z-10 flex min-h-[100dvh] flex-col items-center justify-center px-6 py-12 md:py-16">
        
        {/* Core Hierarchy Stack */}
        <div className="flex flex-col items-center w-full max-w-4xl">
          
          {/* Orb (Centered, tied to heading) */}
          <div className="w-full flex justify-center mb-2 md:-mb-2">
            <Orb state={orbState} />
          </div>
          
          {/* Heading */}
          <div className="w-full flex justify-center mb-3">
            <VaporHeading text="Tamil that sounds human." />
          </div>
          
          {/* Description */}
          <motion.p 
            initial={{ opacity: 0, filter: 'blur(10px)', y: 10 }}
            animate={{ opacity: 1, filter: 'blur(0px)', y: 0 }}
            transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1], delay: 0.4 }}
            className="text-sm md:text-base text-white/40 font-light px-4 text-center max-w-xl leading-relaxed"
          >
            Conversational rendering for emotionally believable Tamil speech synthesis.
          </motion.p>
          
          {/* Input Bar & Absolute Subtitles */}
          <div className="relative w-full max-w-[620px] mt-10 mb-6">
            <VoiceConsole 
              onSubmit={handlePromptSubmit} 
              isProcessing={orbState !== 'idle'} 
            />
            
            {/* Cinematic Subtitles (Ephemeral, Absolute) */}
            <div className="absolute top-full left-0 w-full mt-2 flex justify-center text-center pointer-events-none z-50">
              <AnimatePresence mode="wait">
                {orbState === 'listening' && (
                  <motion.div
                    key="listening"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1 }}
                    className="text-white/20 text-[10px] font-mono uppercase tracking-widest"
                  >
                    Rendering conversational speech...
                  </motion.div>
                )}
                
                {orbState === 'speaking' && subtitleText && (
                  <motion.div
                    key="speaking"
                    initial={{ opacity: 0, y: 4, filter: 'blur(4px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, y: -4, filter: 'blur(4px)' }}
                    transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
                    className="text-white/90 text-sm md:text-base font-light tracking-wide leading-relaxed px-4"
                    style={{ textShadow: "0 0 15px rgba(255,255,255,0.2)" }}
                  >
                    "{subtitleText}"
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
          
          {/* Pipeline Animation */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.5, delay: 0.8 }}
            className="w-full flex justify-center mb-4"
          >
            <PipelineAnimation />
          </motion.div>
          
          {/* Subtle scroll hint */}
          <div className="text-white/20 text-xs font-mono tracking-widest uppercase animate-pulse">
            Scroll to explore
          </div>
          
        </div>
        
      </section>

      {/* ── DEMO SECTION ── */}
      <section className="relative z-20 bg-black/50 backdrop-blur-3xl border-t border-white/5">
        <DemoSection />
      </section>

    </main>
  );
}
