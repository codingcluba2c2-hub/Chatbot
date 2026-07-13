import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, ArrowDown } from 'lucide-react';
import { ChatMessage, MessageProps } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';
import { ThinkingIndicator } from './ThinkingIndicator';
import { isSameDay, format } from 'date-fns';

interface ChatBodyProps {
  messages: MessageProps[];
  botState: 'idle' | 'thinking' | 'typing';
  onSuggestionClick: (suggestion: string) => void;
  onReplayMessage?: (id: string) => void;
  onAction?: (action: string, payload?: any) => void;
}

export const ChatBody: React.FC<ChatBodyProps> = ({ messages, botState, onSuggestionClick, onReplayMessage, onAction }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    if (!showScrollButton || botState !== 'idle') {
      scrollToBottom();
    }
  }, [messages, botState]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShowScrollButton(!isNearBottom);
  };

  return (
    <div 
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 bg-[var(--color-background)]/50 flex flex-col relative transition-colors duration-300"
    >
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center mt-4 mb-10">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/40 dark:to-blue-800/40 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 mb-5 shadow-sm border border-blue-50 dark:border-blue-800/50"
          >
            <Bot size={40} />
          </motion.div>
          <motion.h2 
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-xl sm:text-2xl font-bold text-[var(--color-text-main)] mb-2"
          >
            AI Assistant
          </motion.h2>
          <motion.p 
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-[var(--color-secondary)] max-w-sm mb-8"
          >
            Hello! I'm your Enterprise AI Assistant. I can help you with:
          </motion.p>
        </div>
      ) : (
        <div className="flex flex-col gap-2 pb-4">
          <AnimatePresence initial={false}>
            {messages.map((msg, index) => {
              const showDateDivider = index === 0 || !isSameDay(new Date(msg.timestamp), new Date(messages[index - 1].timestamp));
              
              let dateDividerText = "";
              if (showDateDivider) {
                const today = new Date();
                const msgDate = new Date(msg.timestamp);
                if (isSameDay(msgDate, today)) {
                  dateDividerText = "Today";
                } else {
                  dateDividerText = format(msgDate, "EEEE, MMM d");
                }
              }

              return (
                <React.Fragment key={msg.id}>
                  {showDateDivider && (
                     <div className="flex justify-center my-6">
                       <span className="text-xs font-medium text-[var(--color-secondary)] bg-[var(--color-cards)] px-3 py-1 rounded-full shadow-sm border border-[var(--color-border)]">
                         {dateDividerText}
                       </span>
                     </div>
                  )}
                  <ChatMessage 
                    {...msg} 
                    onReplay={onReplayMessage && msg.trace ? () => onReplayMessage(msg.id) : undefined} 
                    onAction={onAction}
                  />
                </React.Fragment>
              );
            })}
            
            {botState === 'thinking' && (
              <motion.div key="thinking" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <ThinkingIndicator />
              </motion.div>
            )}
            
            {botState === 'typing' && (
              <motion.div key="typing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <TypingIndicator />
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} className="h-4" />
        </div>
      )}
      
      {/* Floating Scroll Button */}
      <AnimatePresence>
        {showScrollButton && messages.length > 0 && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            onClick={() => scrollToBottom()}
            className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-4 py-2 bg-[var(--color-cards)]/90 backdrop-blur-sm border border-[var(--color-border)] shadow-md rounded-full text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-gray-50 dark:hover:bg-slate-800 hover:text-blue-700 dark:hover:text-blue-300 transition-colors z-30"
          >
            <ArrowDown size={14} /> New Messages
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
};
