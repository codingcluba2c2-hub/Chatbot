import React, { useEffect, useState } from 'react';
import { MoreVertical, Maximize2, Minimize2, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tooltip } from './Tooltip';
import { useTheme } from 'next-themes';

interface ChatHeaderProps {
  status?: 'online' | 'offline';
  model?: string;
  latency?: number;
  isExpanded?: boolean;
  onExpandClick?: () => void;
  onRefreshClick: () => void;
  onClose?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ 
  status = 'online', 
  isExpanded,
  onExpandClick,
  onRefreshClick,
  onClose
}) => {
  return (
    <div className="flex items-center justify-between px-4 md:px-6 pb-4 md:pb-6 pt-4 md:pt-5 bg-[#0082FB] text-white rounded-b-[2rem] shadow-sm z-10 sticky top-0 transition-colors duration-300">
      {/* Left section */}
      <div className="flex items-center gap-2 md:gap-3 mt-1">
        <div className="relative">
          <div className="flex items-center justify-center w-[36px] h-[36px] md:w-[46px] md:h-[46px] bg-white rounded-full shadow-sm text-blue-600">
            <span className="font-bold text-xl md:text-3xl italic tracking-tighter" style={{ fontFamily: 'Georgia, serif' }}>M</span>
          </div>
        </div>
        <div className="flex flex-col justify-center">
          <h1 className="font-bold text-[14px] md:text-[16px] text-white tracking-tight leading-tight">
            Mobiloitte
          </h1>
          <p className="text-white/80 text-[10px] md:text-[11px] font-medium flex items-center gap-1.5 mt-0.5">
            <span className={status === 'online' ? "text-[#4ADE80]" : "text-red-400"}>
              ●
            </span>
            <span className={status === 'online' ? "text-[#4ADE80]" : "text-red-400"}>
              {status === 'online' ? "We're online!" : "Offline"}
            </span>
          </p>
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-2 mt-1">
        <Tooltip content="Options">
          <button 
            onClick={onRefreshClick}
            className="w-8 h-8 flex items-center justify-center bg-white/10 hover:bg-white/20 rounded-full transition-colors border border-white/10"
            aria-label="Options"
          >
            <MoreVertical size={15} />
          </button>
        </Tooltip>

        {onExpandClick && (
          <Tooltip content={isExpanded ? "Minimize" : "Expand"}>
            <button 
              onClick={onExpandClick}
              className="w-8 h-8 flex items-center justify-center bg-white/10 hover:bg-white/20 rounded-full transition-colors border border-white/10"
              aria-label={isExpanded ? "Minimize" : "Expand"}
            >
              {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            </button>
          </Tooltip>
        )}
        
        {onClose && (
           <Tooltip content="Close">
             <button 
               onClick={onClose}
               className="w-8 h-8 flex items-center justify-center bg-white/10 hover:bg-white/20 rounded-full transition-colors border border-white/10"
               aria-label="Close"
             >
               <X size={15} />
             </button>
           </Tooltip>
        )}
      </div>
    </div>
  );
};

