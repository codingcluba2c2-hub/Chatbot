import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Send, Menu, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { Tooltip } from './Tooltip';
import { VoiceButton } from './voice/VoiceButton';
import { VoiceTranscript } from './voice/VoiceTranscript';
import { VoiceSettings } from './voice/VoiceSettings';
import { VoiceState, SpeechSettings } from '../../types/speech';
import { Settings2 } from 'lucide-react';
import { useState } from 'react';

export interface InputAreaRef {
  focus: () => void;
}

interface InputAreaProps {
  input: string;
  setInput: (val: string) => void;
  handleSend: (e: React.FormEvent) => void;
  isLoading: boolean;
  onSuggestionClick: (suggestion: string) => void;
  // Voice Props
  voiceState: VoiceState;
  onVoiceToggle: () => void;
  onVoiceCancel: () => void;
  voiceTranscript: string;
  speechSettings: SpeechSettings;
  setSpeechSettings: React.Dispatch<React.SetStateAction<SpeechSettings>>;
  voices: SpeechSynthesisVoice[];
}

export const InputArea = forwardRef<InputAreaRef, InputAreaProps>(({ 
  input, setInput, handleSend, isLoading, onSuggestionClick,
  voiceState, onVoiceToggle, onVoiceCancel, voiceTranscript,
  speechSettings, setSpeechSettings, voices
}, ref) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showSettings, setShowSettings] = useState(false);

  useImperativeHandle(ref, () => ({
    focus: () => {
      textareaRef.current?.focus();
    }
  }));

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        handleSend(e as unknown as React.FormEvent);
      }
    } else if (e.key === 'Escape') {
      setInput('');
      textareaRef.current?.blur();
    }
  };

  return (
    <div className="bg-white dark:bg-[#0a0f1c] p-4 pt-2 relative z-20 transition-colors duration-300">

      {/* Input Form */}
      <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-white dark:bg-slate-900 border-2 border-gray-200/80 dark:border-slate-700/80 rounded-3xl px-3 py-1.5 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all duration-300">

        {/* Textarea or Voice Transcript */}
        {voiceState === 'idle' ? (
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Type your message..."
            rows={1}
            className="flex-1 max-h-[120px] bg-transparent border-none resize-none focus:outline-none focus:ring-0 text-[13px] md:text-[14px] py-2 px-2 custom-scrollbar placeholder:text-gray-400 dark:placeholder:text-gray-500 text-gray-800 dark:text-gray-100 font-medium leading-relaxed"
          />
        ) : (
          <div className="flex-1">
            <VoiceTranscript 
              transcript={voiceTranscript}
              state={voiceState}
              onCancel={onVoiceCancel}
            />
          </div>
        )}

        {/* Right Actions */}
        <div className="mb-0.5 mr-0.5 flex items-center gap-1">
          <div className="hidden sm:flex items-center gap-1 relative">
            <button 
              type="button" 
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-full mr-1 transition-colors"
            >
              <Settings2 size={16} />
            </button>
            {showSettings && (
              <div className="absolute bottom-full mb-2 right-0 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 z-[100]">
                <VoiceSettings 
                  settings={speechSettings}
                  setSettings={setSpeechSettings}
                  voices={voices}
                />
              </div>
            )}
            <VoiceButton state={voiceState} onClick={onVoiceToggle} />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={cn(
              "flex items-center justify-center w-[38px] h-[38px] rounded-full transition-all duration-300",
              !input.trim() || isLoading
                ? "bg-gray-100 dark:bg-slate-800 text-gray-400 dark:text-gray-500"
                : "bg-[#0082FB] hover:bg-blue-600 text-white shadow-sm hover:scale-105 active:scale-95"
            )}
            aria-label="Send message"
          >
            {isLoading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
              />
            ) : (
              <Send size={16} className="-ml-0.5" />
            )}
          </button>
        </div>
      </form>
      
      {/* Footer Text */}
      <div className="mt-3 flex justify-center items-center text-[10px] text-gray-400 font-medium gap-1">
        <a href="#" className="hover:text-blue-500 transition-colors">Privacy & Policy</a>
        <span className="text-gray-300">|</span>
        <span>Powered By <span className="font-semibold text-gray-500">Converiqo.ai</span></span>
      </div>
    </div>
  );
});
InputArea.displayName = 'InputArea';
