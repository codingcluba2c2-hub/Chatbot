import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { VoiceWave } from './VoiceWave';
import { X } from 'lucide-react';
import { VoiceState } from '../../../types/speech';

interface VoiceTranscriptProps {
  transcript: string;
  state: VoiceState;
  onCancel: () => void;
}

export const VoiceTranscript: React.FC<VoiceTranscriptProps> = ({ transcript, state, onCancel }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-center w-full h-[38px] px-2"
    >
      <div className="flex-1 flex items-center overflow-hidden mr-2 relative h-full">
        <AnimatePresence mode="wait">
          {!transcript && state === 'listening' ? (
            <motion.div
              key="listening"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center text-blue-500 font-medium text-[13px] md:text-[14px] w-full"
            >
              Listening...
              <div className="ml-auto mr-4">
                <VoiceWave isListening={true} isSpeaking={false} color="bg-blue-500" />
              </div>
            </motion.div>
          ) : !transcript && state === 'recognizing' ? (
             <motion.div
              key="recognizing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center text-blue-500 font-medium text-[13px] md:text-[14px] w-full"
            >
              Recognizing...
              <div className="ml-auto mr-4">
                <VoiceWave isListening={true} isSpeaking={false} color="bg-blue-500" />
              </div>
            </motion.div>
          ) : !transcript && (state === 'sending' || state === 'waiting_response') ? (
             <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center text-purple-500 font-medium text-[13px] md:text-[14px] w-full"
            >
              {state === 'sending' ? 'Sending...' : 'Waiting for response...'}
            </motion.div>
          ) : !transcript && state === 'speaking' ? (
             <motion.div
              key="speaking"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center text-emerald-500 font-medium text-[13px] md:text-[14px] w-full"
            >
              Speaking...
              <div className="ml-auto mr-4">
                <VoiceWave isListening={false} isSpeaking={true} color="bg-emerald-500" />
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="transcript"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center text-gray-800 dark:text-gray-100 font-medium text-[13px] md:text-[14px] truncate w-full"
            >
              {transcript}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <button
        type="button"
        onClick={onCancel}
        className="p-1.5 text-gray-400 hover:text-red-500 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors shrink-0"
        aria-label="Cancel Voice"
      >
        <X size={16} />
      </button>
    </motion.div>
  );
};
