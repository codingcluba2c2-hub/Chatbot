import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Bot, Loader2 } from 'lucide-react';

export const ThinkingIndicator = () => {
  const [loadingText, setLoadingText] = useState('Analyzing query...');
  
  useEffect(() => {
    const statuses = [
      'Analyzing query...',
      'Searching knowledge base...',
      'Synthesizing response...',
      'Finalizing...'
    ];
    let i = 0;
    const interval = setInterval(() => {
      i = (i + 1) % statuses.length;
      setLoadingText(statuses[i]);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex w-full mt-4 space-x-3 max-w-[80%]"
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-50 to-blue-100 dark:from-slate-800 dark:to-slate-700 border border-blue-200/50 dark:border-slate-600 shadow-sm flex items-center justify-center text-blue-600 dark:text-blue-400 mt-auto">
        <Bot size={16} />
      </div>
      <div className="flex flex-col mb-1 w-64 max-w-full">
        <div className="bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700/80 shadow-sm rounded-2xl rounded-bl-sm p-3 w-full flex flex-col gap-2.5">
          
          <div className="flex items-center justify-between text-[13px]">
            <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-300 font-medium">
              <Loader2 size={13} className="animate-spin text-blue-500" />
              <span>{loadingText}</span>
            </div>
          </div>

          {/* Progress Bar Container */}
          <div className="w-full h-1.5 bg-gray-100 dark:bg-slate-700/50 rounded-full overflow-hidden relative">
            {/* Animated Progress Fill */}
            <motion.div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full"
              initial={{ width: "0%" }}
              animate={{ width: ["0%", "30%", "65%", "85%", "94%"] }}
              transition={{ 
                duration: 6, 
                ease: "easeOut",
                times: [0, 0.15, 0.4, 0.7, 1] 
              }}
            />
          </div>

        </div>
      </div>
    </motion.div>
  );
};
