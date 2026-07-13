import React from 'react';
import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

export const TypingIndicator = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex w-full mt-4 space-x-3 max-w-[80%]"
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 shadow-sm flex items-center justify-center text-blue-600 mt-auto">
        <Bot size={16} />
      </div>
      <div className="flex flex-col mb-1">
        <span className="text-xs text-gray-500 mb-1 ml-1 flex items-center gap-1">
          <Bot size={12} /> AI is typing...
        </span>
        <div className="bg-white border border-[var(--color-border)] shadow-sm rounded-2xl rounded-bl-sm p-4 text-[var(--color-text-main)] w-fit flex items-center h-[42px]">
          <div className="flex space-x-1.5 items-center">
            <motion.div
              className="w-2 h-2 bg-gray-400 rounded-full"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
            />
            <motion.div
              className="w-2 h-2 bg-gray-400 rounded-full"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
            />
            <motion.div
              className="w-2 h-2 bg-gray-400 rounded-full"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
};
