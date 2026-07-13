import React from 'react';

export const ActionButtons = ({ buttons, onClick }: { buttons: any[], onClick: (action: string) => void }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {buttons.map((btn, idx) => (
        <button
          key={idx}
          onClick={() => onClick(btn.action)}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white shadow-sm"
        >
          {btn.text}
        </button>
      ))}
    </div>
  );
};
