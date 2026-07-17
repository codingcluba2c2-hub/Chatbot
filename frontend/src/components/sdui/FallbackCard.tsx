import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const FallbackCard = ({
  fallback,
  onAction,
}: {
  fallback: any;
  onAction: (action: string, payload?: any) => void;
}) => {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl border border-yellow-200/50 bg-[#FFFCF5] shadow-sm mb-2 w-full max-w-[90%] md:max-w-md">
      <div className="text-sm text-slate-700 leading-relaxed">
        {fallback.prefix || "I couldn't find any information related to"} 
        <strong>"{fallback.query}"</strong>
        {fallback.suffix || "in the current enterprise knowledge base."}
      </div>

      <div className="flex flex-wrap gap-2 mt-2">
        {fallback.suggestions?.map((suggestion: string, idx: number) => (
          <button
            key={idx}
            onClick={() => onAction('send_message', { text: suggestion })}
            className="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-full hover:bg-blue-100 transition-colors cursor-pointer"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};
