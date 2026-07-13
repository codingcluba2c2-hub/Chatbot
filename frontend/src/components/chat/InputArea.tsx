import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Send, Paperclip, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { Tooltip } from './Tooltip';
import { SuggestionBar } from './SuggestionBar';

export interface InputAreaRef {
  focus: () => void;
}

interface InputAreaProps {
  input: string;
  setInput: (val: string) => void;
  handleSend: (e: React.FormEvent) => void;
  isLoading: boolean;
  onSuggestionClick: (suggestion: string) => void;
}

export const InputArea = forwardRef<InputAreaRef, InputAreaProps>(({ input, setInput, handleSend, isLoading, onSuggestionClick }, ref) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
    <div className="bg-[var(--color-cards)]/80 backdrop-blur-md border-t border-[var(--color-border)] p-3 sm:p-4 sm:rounded-b-2xl shadow-sm relative z-20 transition-colors duration-300">
      
      <SuggestionBar isVisible={input.trim() === ''} onSuggestionClick={onSuggestionClick} />

      {/* Input Form */}
      <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-[var(--color-background)] border border-[var(--color-border)] rounded-2xl p-1.5 shadow-inner focus-within:bg-[var(--color-cards)] focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all duration-300">
        
        {/* Left Actions */}
        <div className="flex items-center gap-1 mb-1 sm:mb-1.5 ml-1">
          <Tooltip content="File upload coming soon">
            <button type="button" className="p-2 text-gray-300 cursor-not-allowed rounded-full" aria-label="Attach file">
              <Paperclip size={20} />
            </button>
          </Tooltip>
          <div className="hidden sm:block">
            <Tooltip content="Voice input coming soon">
              <button type="button" className="p-2 text-gray-300 cursor-not-allowed rounded-full" aria-label="Voice input">
                <Mic size={20} />
              </button>
            </Tooltip>
          </div>
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type your message... (Press '/' to focus)"
          disabled={isLoading}
          rows={1}
          className="flex-1 max-h-[120px] bg-transparent border-none resize-none focus:outline-none focus:ring-0 text-sm sm:text-[0.95rem] py-2 px-2 custom-scrollbar placeholder:text-gray-400 dark:placeholder:text-gray-500"
        />

        {/* Right Actions */}
        <div className="mb-1 sm:mb-1.5 mr-1">
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={cn(
              "flex items-center justify-center p-2.5 rounded-xl transition-all shadow-sm",
              !input.trim() || isLoading
                ? "bg-[var(--color-border)] text-[var(--color-secondary)] cursor-not-allowed"
                : "bg-gradient-to-br from-blue-600 to-blue-700 text-white hover:shadow-md hover:-translate-y-0.5 active:translate-y-0"
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
              <Send size={18} className="ml-0.5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
});
InputArea.displayName = 'InputArea';
