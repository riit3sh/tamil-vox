"use client";

import React, { useState } from 'react';
import { Play, Pause } from 'lucide-react';
import { motion } from 'framer-motion';

const EXAMPLES = [
  {
    input: "phone charge illa da",
    raw_tts: "என்னுடைய தொலைபேசியில் மின்சாரம் இல்லை.",
    tamilvox: "mmm... charge பண்ணி வச்சிருக்கேன்..."
  },
  {
    input: "dei sema mokka da",
    raw_tts: "நண்பரே, இது மிகவும் சலிப்பாக இருக்கிறது.",
    tamilvox: "அட டேய்... செம மொக்க தான்..."
  },
  {
    input: "padikka ukkandha udane thookam vandhuruchu",
    raw_tts: "நான் படிக்க அமர்ந்தவுடன் எனக்கு உறக்கம் வந்துவிட்டது.",
    tamilvox: "ஆன்... உடனே தூக்கம் வந்துருச்சு..."
  }
];

function AudioCard({ title, text, isActive, type, onPlay }: { title: string, text: string, isActive: boolean, type: 'raw' | 'vox', onPlay: () => void }) {
  const isVox = type === 'vox';
  
  return (
    <div className={`glass-panel p-8 flex flex-col gap-8 flex-1 min-w-[300px] relative overflow-hidden group transition-all duration-500 ${!isVox && 'opacity-80 saturate-50'}`}>
      {/* Subtle glow orb inside card - only for vox */}
      {isVox && (
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl group-hover:bg-cyan-500/20 transition-colors duration-700" />
      )}
      
      <h3 className={`text-sm font-mono tracking-widest uppercase ${isVox ? 'text-cyan-400/80' : 'text-white/40'}`}>
        {title}
      </h3>
      
      <div className="flex-1 flex items-center min-h-[100px]">
        <p className={`text-xl md:text-2xl font-light leading-relaxed ${isVox ? 'text-white' : 'text-white/70'}`}>
          "{text}"
        </p>
      </div>

      <div className="flex items-center gap-6 mt-4">
        <button 
          onClick={onPlay}
          className={`glass-button w-14 h-14 ${isVox ? 'bg-cyan-500/10 text-cyan-100 hover:bg-cyan-500/20 shadow-[0_0_15px_rgba(0,255,255,0.1)]' : 'bg-white/5 text-white/70'}`}
        >
          {isActive ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-1" />}
        </button>

        {/* Mock Waveform */}
        <div className="flex-1 flex items-center gap-1 h-8">
          {[...Array(24)].map((_, i) => (
            <motion.div
              key={i}
              className={`w-1 rounded-full ${isVox ? 'bg-cyan-400/60 shadow-[0_0_8px_rgba(0,255,255,0.4)]' : 'bg-white/20'}`}
              initial={{ height: "20%" }}
              animate={{ 
                height: isActive ? `${Math.max(20, Math.random() * 100)}%` : "20%" 
              }}
              transition={{
                duration: 0.1,
                repeat: isActive ? Infinity : 0,
                repeatType: "reverse"
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export function DemoSection() {
  const [playingId, setPlayingId] = useState<string | null>(null);

  const togglePlay = (id: string) => {
    setPlayingId(playingId === id ? null : id);
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-6 py-20 flex flex-col gap-16 relative z-10">
      
      <div className="space-y-16">
        {EXAMPLES.map((example, idx) => (
          <div key={idx} className="flex flex-col gap-6">
            <div className="text-sm font-mono text-white/30 pl-4 border-l-2 border-white/10 uppercase tracking-widest">
              Input: {example.input}
            </div>
            
            <div className="flex flex-col md:flex-row gap-6">
              <AudioCard 
                title="Raw Tamil TTS"
                text={example.raw_tts}
                type="raw"
                isActive={playingId === `raw-${idx}`}
                onPlay={() => togglePlay(`raw-${idx}`)}
              />
              <AudioCard 
                title="Tamilvox"
                text={example.tamilvox}
                type="vox"
                isActive={playingId === `vox-${idx}`}
                onPlay={() => togglePlay(`vox-${idx}`)}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
