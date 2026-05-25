"use client";

import React, { useState } from 'react';
import { Orb } from '@/components/Orb';
import { VoiceConsole } from '@/components/VoiceConsole';
import { PipelineAnimation } from '@/components/PipelineAnimation';
import { DemoSection } from '@/components/DemoSection';
import { Github } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Home() {
  const [orbState, setOrbState] = useState<'idle' | 'listening' | 'speaking'>('idle');

  const handlePromptSubmit = async (prompt: string) => {
    setOrbState('listening');
    
    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: prompt })
      });
      
      const data = await response.json();
      
      if (data.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
        audio.onended = () => {
          setOrbState('idle');
        };
        audio.play().catch(e => {
          console.error("Audio playback failed:", e);
          setOrbState('idle');
        });
        setOrbState('speaking');
      } else {
        setOrbState('idle');
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
      <section className="relative w-full h-[100dvh] min-h-[750px] flex flex-col items-center justify-center pt-10 pb-32">
        
        {/* Center Orb */}
        <div className="flex flex-col items-center justify-center z-10 w-full px-4 -mt-10">
          <div className="text-[10px] md:text-xs uppercase tracking-[0.3em] text-white/30 font-mono text-center mb-8">
            Experimental Speech Rendering System
          </div>
          
          <div className="my-[-20px] md:my-[-40px]">
            <Orb state={orbState} />
          </div>
          
          <div className="flex flex-col items-center text-center mt-8 md:mt-12 w-full max-w-3xl">
            <motion.h1 
              initial={{ opacity: 0, filter: 'blur(12px)', scale: 0.98, y: 10 }}
              animate={{ opacity: 1, filter: 'blur(0px)', scale: 1, y: 0 }}
              transition={{ duration: 2.0, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
              className="text-3xl md:text-5xl lg:text-6xl font-extralight tracking-tight text-white/90 leading-tight"
            >
              Tamil that sounds human.
            </motion.h1>
            <motion.p 
              initial={{ opacity: 0, filter: 'blur(12px)', scale: 0.98, y: 10 }}
              animate={{ opacity: 1, filter: 'blur(0px)', scale: 1, y: 0 }}
              transition={{ duration: 2.0, ease: [0.16, 1, 0.3, 1], delay: 0.6 }}
              className="text-sm md:text-lg text-white/40 font-light mt-4 px-2"
            >
              Conversational rendering for emotionally believable Tamil speech synthesis.
            </motion.p>
            <motion.div 
              initial={{ opacity: 0, filter: 'blur(10px)' }}
              animate={{ opacity: 1, filter: 'blur(0px)' }}
              transition={{ duration: 2.0, ease: [0.16, 1, 0.3, 1], delay: 1.0 }}
              className="mt-8"
            >
              <PipelineAnimation />
            </motion.div>
          </div>
        </div>

        {/* Floating Voice Console */}
        <VoiceConsole 
          onSubmit={handlePromptSubmit} 
          isProcessing={orbState !== 'idle'} 
        />
        
        {/* Subtle scroll hint */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 text-white/20 text-xs font-mono tracking-widest uppercase animate-pulse">
          Scroll to explore
        </div>
      </section>

      {/* ── DEMO SECTION ── */}
      <section className="relative z-20 bg-black/50 backdrop-blur-3xl border-t border-white/5">
        <DemoSection />
      </section>

    </main>
  );
}
