import React from 'react';
import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

export const ThinkingIndicator = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex w-full mt-4 space-x-3 max-w-[80%]"
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 border border-gray-300 shadow-sm flex items-center justify-center text-gray-500 mt-auto">
        <Bot size={16} />
      </div>
      <div className="flex flex-col mb-1">
        <div className="bg-gray-100 border border-[var(--color-border)] shadow-sm rounded-2xl rounded-bl-sm px-4 py-2 text-gray-500 w-fit flex items-center">
          <motion.span
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            className="text-sm font-medium"
          >
            Thinking...
          </motion.span>
        </div>
      </div>
    </motion.div>
  );
};
