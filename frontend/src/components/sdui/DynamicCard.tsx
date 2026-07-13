import React from 'react';
import { ActionButtons } from './ActionButtons';

export const DynamicCard = ({ card, onAction }: { card: any, onAction: (action: string) => void }) => {
  return (
    <div className="w-full max-w-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
      {card.image_url && (
        <img src={card.image_url} alt={card.title} className="w-full h-32 object-cover" />
      )}
      <div className="p-4">
        <h3 className="font-bold text-slate-900 dark:text-slate-100">{card.title}</h3>
        {card.subtitle && <p className="text-xs text-blue-600 dark:text-blue-400 font-medium mt-1 uppercase tracking-wider">{card.subtitle}</p>}
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">{card.description}</p>
        
        {card.buttons && card.buttons.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <ActionButtons buttons={card.buttons} onClick={onAction} />
          </div>
        )}
      </div>
    </div>
  );
};
