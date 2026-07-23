import React from 'react';
import { motion } from 'framer-motion';

interface VoiceWaveProps {
  isSpeaking: boolean;
  isListening: boolean;
  color?: string;
}

export const VoiceWave: React.FC<VoiceWaveProps> = ({ isSpeaking, isListening, color = "bg-blue-500" }) => {
  const bars = Array.from({ length: 5 });

  if (!isSpeaking && !isListening) return null;

  return (
    <div className="flex items-center justify-center gap-[3px] h-[24px]">
      {bars.map((_, i) => (
        <motion.div
          key={i}
          className={`w-[3px] rounded-full ${color}`}
          animate={{
            height: isSpeaking ? ["4px", "16px", "4px"] : isListening ? ["4px", "12px", "4px"] : "4px",
          }}
          transition={{
            duration: isSpeaking ? 0.6 : 1.2,
            repeat: Infinity,
            delay: i * 0.1,
            ease: "easeInOut",
          }}
          style={{
            originY: 0.5
          }}
        />
      ))}
    </div>
  );
};
