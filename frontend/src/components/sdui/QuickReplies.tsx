import React from 'react';

export const QuickReplies = ({ items, onSelect }: { items: string[], onSelect: (text: string) => void }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(item)}
          className="px-4 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 border border-blue-200 rounded-full text-sm font-medium transition-colors dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50 dark:hover:bg-blue-900/50"
        >
          {item}
        </button>
      ))}
    </div>
  );
};
