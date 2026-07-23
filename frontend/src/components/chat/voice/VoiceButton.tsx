import React from 'react';
import { Mic, Square, Loader2, Volume2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { VoiceState } from '../../../types/speech';
import { Tooltip } from '../Tooltip';

interface VoiceButtonProps {
  state: VoiceState;
  onClick: () => void;
  disabled?: boolean;
}

export const VoiceButton: React.FC<VoiceButtonProps> = ({ state, onClick, disabled }) => {
  return (
    <Tooltip content={state === 'idle' ? 'Voice Input' : (state === 'listening' || state === 'recognizing') ? 'Stop Listening' : state === 'speaking' ? 'Stop Speaking' : 'Processing...'}>
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || ['sending', 'waiting_response'].includes(state)}
        className={`relative flex items-center justify-center w-[38px] h-[38px] rounded-full transition-all duration-300 ${
          (state === 'listening' || state === 'recognizing')
            ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400' 
            : state === 'speaking'
            ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400'
            : 'bg-transparent text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-800'
        }`}
      >
        <AnimatePresence mode="wait">
          {state === 'idle' && (
            <motion.div
              key="idle"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Mic size={18} />
            </motion.div>
          )}

          {(state === 'listening' || state === 'recognizing') && (
            <motion.div
              key="listening"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="relative flex items-center justify-center w-full h-full"
            >
              <motion.div
                className="absolute inset-0 rounded-full bg-blue-400/30 dark:bg-blue-500/20"
                animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
              />
              <Square size={14} className="fill-current" />
            </motion.div>
          )}

          {['sending', 'waiting_response'].includes(state) && (
            <motion.div
              key="processing"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Loader2 size={18} className="animate-spin text-blue-500" />
            </motion.div>
          )}

          {state === 'speaking' && (
            <motion.div
              key="speaking"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="relative flex items-center justify-center w-full h-full"
            >
               <motion.div
                className="absolute inset-0 rounded-full bg-emerald-400/30 dark:bg-emerald-500/20"
                animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              />
              <Square size={14} className="fill-current" />
            </motion.div>
          )}
        </AnimatePresence>
      </button>
    </Tooltip>
  );
};
