import React from 'react';

export const QuickReplies = ({ items, onSelect }: { items: string[], onSelect: (text: string) => void }) => {
  return (
    <div className="grid grid-cols-2 gap-2 mt-2 w-full">
      {items.map((item, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(item)}
          aria-label={`Send message: ${item}`}
          className="px-3 py-2 bg-blue-50/80 hover:bg-blue-100 text-blue-700 border border-blue-200/80 rounded-full text-[13px] md:text-[14px] font-medium transition-all duration-200 shadow-sm hover:shadow dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-700/50 dark:hover:bg-blue-800/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 dark:focus:ring-offset-slate-900 truncate"
        >
          {item}
        </button>
      ))}
    </div>
  );
};
