import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowDown, Calendar, LayoutGrid, Briefcase, Mail, CheckSquare, Star } from 'lucide-react';
import { ChatMessage, MessageProps } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';
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

  const suggestions = [
    { icon: <Calendar size={16} />, text: "Office Timings" },
    { icon: <LayoutGrid size={16} />, text: "Our Services" },
    { icon: <Briefcase size={16} />, text: "Career Opportunities" },
    { icon: <Mail size={16} />, text: "Contact Us" },
    { icon: <CheckSquare size={16} />, text: "Projects Completed" },
    { icon: <Star size={16} />, text: "Client Satisfaction" },
  ];

  return (
    <div 
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto custom-scrollbar px-4 py-6 bg-white dark:bg-[#0a0f1c] flex flex-col relative transition-colors duration-300"
    >
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col justify-start pt-2 w-full relative z-10">
          
          {/* Initial Welcome Message matching screenshot */}
          <div className="flex w-full mb-8 space-x-4 justify-start">
            <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 shadow-md flex items-center justify-center text-white mt-1 z-10 border border-blue-500/30">
              <span className="font-bold text-lg italic tracking-tighter" style={{ fontFamily: 'Georgia, serif' }}>M</span>
            </div>
            <div className="flex flex-col max-w-[80%] items-start">
              <div className="relative px-5 py-4 text-[14px] md:text-[15px] xl:text-[16px] leading-relaxed break-words whitespace-pre-wrap transition-all duration-300 bg-white border border-gray-200/60 text-gray-800 rounded-2xl rounded-tl-sm dark:bg-[#1E293B] dark:border-slate-700/50 dark:text-gray-100 shadow-sm hover:shadow-md">
                Hi, I am Mobiloitte's virtual agent.<br/>How can I help you today?
                <div className="flex justify-end text-[0.7rem] text-gray-400 dark:text-gray-500 mt-2 font-medium tracking-wide" suppressHydrationWarning>
                  {format(new Date(), 'h:mm a')}
                </div>
              </div>
            </div>
          </div>
          
          <motion.div 
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="grid grid-cols-2 gap-2 w-full mx-auto"
          >
            {suggestions.map((item, idx) => (
               <button 
                 key={idx}
                 onClick={() => onSuggestionClick(item.text)}
                 className="flex items-center justify-center gap-2 px-3 py-3 bg-[#0082FB] hover:bg-blue-600 text-white rounded-xl transition-all shadow-sm font-semibold text-[11px] md:text-[12px] xl:text-[13px]"
               >
                 {item.icon}
                 <span>{item.text}</span>
               </button>
            ))}
          </motion.div>
        </div>
      ) : (
        <div className="flex flex-col gap-4 pb-4 relative z-10">
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

              const isEmpty = !msg.content && (!msg.components || msg.components.length === 0) && msg.role === 'bot';
              
              return (
                <React.Fragment key={msg.id}>
                  {showDateDivider && (
                     <div className="flex justify-center my-6">
                       <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest bg-white dark:bg-slate-800 px-4 py-1.5 rounded-full shadow-sm border border-gray-100 dark:border-slate-700/50">
                         {dateDividerText}
                       </span>
                     </div>
                  )}
                  {!isEmpty && (
                    <ChatMessage 
                      {...msg} 
                      onReplay={onReplayMessage && msg.trace ? () => onReplayMessage(msg.id) : undefined} 
                      onAction={onAction}
                    />
                  )}
                </React.Fragment>
              );
            })}
            
            {(botState === 'thinking' || botState === 'typing') && (!messages.length || messages[messages.length-1].role !== 'bot' || !messages[messages.length-1].content) && (
              <motion.div key="typing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <TypingIndicator />
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} className="h-4" />
        </div>
      )}
    </div>
  );
};
