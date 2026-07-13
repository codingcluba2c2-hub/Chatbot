import React from 'react';

interface ChatFooterProps {
  messageCount: number;
  avgResponseTime: number;
  status: 'online' | 'offline';
  model: string;
}

export const ChatFooter: React.FC<ChatFooterProps> = ({ messageCount, avgResponseTime, status, model }) => {
  return (
    <div className="hidden sm:flex justify-between items-center px-4 py-2 bg-gray-50/80 border-t border-[var(--color-border)] text-[10px] text-gray-500 font-medium z-10 rounded-b-2xl">
      <div className="flex gap-4">
        <span>Messages : {messageCount}</span>
        <span>Average Response : {avgResponseTime > 0 ? `${avgResponseTime.toFixed(2)} sec` : 'N/A'}</span>
      </div>
      <div className="flex gap-4">
        <span>Backend : {model}</span>
        <span className="flex items-center gap-1">
          Status : 
          <span className={status === 'online' ? 'text-green-600' : 'text-red-600'}>
            {status === 'online' ? 'Connected' : 'Disconnected'}
          </span>
        </span>
      </div>
    </div>
  );
};
