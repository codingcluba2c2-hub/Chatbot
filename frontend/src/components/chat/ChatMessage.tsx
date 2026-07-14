import React from 'react';
import { motion } from 'framer-motion';
import { Bot, User, Check, CheckCheck, Copy, RefreshCw, ThumbsUp, ThumbsDown, Volume2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { Tooltip } from './Tooltip';
import { ComponentRenderer } from '../sdui/ComponentRenderer';

export type MessageProps = {
  id: string;
  role: 'user' | 'bot';
  content: string;
  intent?: string;
  timestamp: number;
  status?: 'sent' | 'delivered' | 'read';
  trace?: any; 
  components?: any[];
  actions?: any[];
  onReplay?: () => void;
  onAction?: (action: string, payload?: any) => void;
};

const getIntentColor = (intent?: string) => {
  if (!intent) return "";
  const lower = intent.toLowerCase();
  if (lower === "greeting") return "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800/50";
  if (lower === "fallback") return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50";
  if (lower === "gibberish") return "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800/50";
  if (lower === "goodbye") return "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50";
  if (lower === "fastpath") return "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800/50";
  return "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700";
};

export const ChatMessage: React.FC<MessageProps> = ({ role, content, intent, timestamp, status, trace, components, actions, onReplay, onAction }) => {
  const isBot = role === 'bot';
  
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={cn("flex w-full mt-4 space-x-3 group", isBot ? "justify-start" : "justify-end")}
    >
      {/* Bot Avatar */}
      {isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center text-blue-600 mt-auto z-10 border border-gray-100 dark:border-slate-800">
          <span className="font-bold text-lg italic tracking-tighter" style={{ fontFamily: 'Georgia, serif' }}>M</span>
        </div>
      )}

      {/* Message Bubble Container */}
      <div className={cn("flex flex-col max-w-[75%]", isBot ? "items-start -ml-1" : "items-end")}>
        
        {/* Name / Badge Row */}
        {isBot && intent && (
          <div className="mb-1.5 ml-2">
            <span className={cn(
              "text-[0.65rem] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border shadow-sm",
              getIntentColor(intent)
            )}>
              {intent.toLowerCase() === 'knowledge' ? 'RAG' : intent.toLowerCase() === 'fallback' ? 'OUT OF SCOPE' : intent}
            </span>
          </div>
        )}

        {/* Bubble */}
        <div className={cn(
          "relative px-4 py-3 rounded-[20px] text-[13px] md:text-[14px] xl:text-[15px] leading-relaxed break-words whitespace-pre-wrap transition-all duration-300",
          isBot 
            ? "bg-white border border-gray-100 text-gray-800 rounded-bl-[4px] dark:bg-slate-800 dark:border-slate-700/60 dark:text-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)]"
            : "bg-[#0082FB] text-white rounded-br-[4px] shadow-sm"
        )}>
          {content.split(/(\*\*.*?\*\*)/g).map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={i} className="font-semibold text-blue-700 dark:text-blue-400">{part.slice(2, -2)}</strong>;
            }
            return part;
          })}
          
          {/* SDUI Components rendering inside the bubble if bot */}
          {isBot && components && components.length > 0 && onAction && (
            <ComponentRenderer components={components} onAction={onAction} />
          )}

          {/* Timestamp and Status inside or below */}
          <div className={cn(
            "flex items-center gap-1 text-[0.65rem] mt-1.5 justify-end opacity-70 font-medium",
            isBot ? "text-gray-400" : "text-blue-100"
          )}>
            <span>{format(new Date(timestamp), 'h:mm a')}</span>
            
            {!isBot && status && (
              <span className="ml-0.5">
                {status === 'sent' && <Check size={12} />}
                {(status === 'delivered' || status === 'read') && <CheckCheck size={12} className={status === 'read' ? 'text-blue-200' : ''} />}
              </span>
            )}
          </div>
        </div>
        
        {/* Actions Toolbar */}
        {isBot && (
          <div className="flex items-center gap-2 mt-1.5 ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <Tooltip content="Helpful">
              <button className="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                <ThumbsUp size={13} />
              </button>
            </Tooltip>
            <Tooltip content="Not Helpful">
              <button className="p-1 text-gray-400 hover:text-red-600 transition-colors">
                <ThumbsDown size={13} />
              </button>
            </Tooltip>
            <Tooltip content="Copy">
              <button onClick={handleCopy} className="p-1 text-gray-400 hover:text-gray-700 transition-colors">
                <Copy size={13} />
              </button>
            </Tooltip>
            <Tooltip content="Listen">
              <button className="p-1 text-gray-400 hover:text-gray-700 transition-colors">
                <Volume2 size={13} />
              </button>
            </Tooltip>
            
            {onReplay && trace && (
              <Tooltip content="Replay Pipeline">
                <button onClick={onReplay} className="p-1 text-emerald-500 hover:text-emerald-700 transition-colors ml-1">
                  <RefreshCw size={13} />
                </button>
              </Tooltip>
            )}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {!isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 shadow-sm flex items-center justify-center text-gray-500 dark:text-gray-400 mt-auto z-10">
          <User size={16} />
        </div>
      )}
    </motion.div>
  );
};

