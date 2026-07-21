import React, { useState } from 'react';
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
  const [isCopied, setIsCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={cn("flex w-full mt-5 space-x-4 group", isBot ? "justify-start" : "justify-end")}
    >
      {/* Bot Avatar */}
      {isBot && (
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 shadow-md flex items-center justify-center text-white mt-1 z-10 border border-blue-500/30">
          <span className="font-bold text-lg italic tracking-tighter" style={{ fontFamily: 'Georgia, serif' }}>M</span>
        </div>
      )}

      {/* Message Bubble Container */}
      <div className={cn("flex flex-col max-w-[80%]", isBot ? "items-start" : "items-end")}>

        {/* Bubble */}
        <div className={cn(
          "relative px-5 py-4 text-[14px] md:text-[15px] xl:text-[16px] leading-relaxed break-words whitespace-pre-wrap transition-all duration-300",
          isBot 
            ? "bg-white border border-gray-200/60 text-gray-800 rounded-2xl rounded-tl-sm dark:bg-[#1E293B] dark:border-slate-700/50 dark:text-gray-100 shadow-sm hover:shadow-md"
            : "bg-gradient-to-br from-[#0f172a] to-[#1e293b] dark:from-blue-600 dark:to-blue-800 border border-slate-700/50 dark:border-blue-500/30 text-white rounded-2xl rounded-tr-sm shadow-md"
        )}>
          {content.split(/(\*\*.*?\*\*|\[.*?\]\(.*?\))/g).map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={i} className="font-semibold text-blue-700 dark:text-blue-400">{part.slice(2, -2)}</strong>;
            }
            if (part.startsWith('[') && part.endsWith(')') && part.includes('](')) {
              const match = part.match(/\[(.*?)\]\((.*?)\)/);
              if (match) {
                return (
                  <a 
                    key={i} 
                    href={match[2]} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-block mt-3 mb-1 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-sm hover:shadow transition-all no-underline w-auto border border-blue-500"
                  >
                    {match[1]}
                  </a>
                );
              }
            }
            return part;
          })}
          
          {/* SDUI Components rendering inside the bubble if bot */}
          {isBot && components && components.length > 0 && onAction && (
            <div className="mt-4 border-t border-gray-100 dark:border-slate-700/50 pt-4">
              <ComponentRenderer components={components} onAction={onAction} />
            </div>
          )}

          {/* Timestamp and Status inside or below */}
          <div className={cn(
            "flex items-center gap-1.5 text-[0.7rem] mt-2 justify-end opacity-70 font-medium tracking-wide",
            isBot ? "text-gray-400 dark:text-gray-500" : "text-gray-300 dark:text-blue-200"
          )}>
            <span>{format(new Date(timestamp), 'h:mm a')}</span>
            
            {!isBot && status && (
              <span className="ml-0.5">
                {status === 'sent' && <Check size={14} />}
                {(status === 'delivered' || status === 'read') && <CheckCheck size={14} className={status === 'read' ? 'text-blue-400' : ''} />}
              </span>
            )}
          </div>
        </div>
        
        {/* Actions Toolbar */}
        <div className={cn(
          "flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200",
          isBot ? "ml-1" : "mr-1 justify-end"
        )}>
          {isBot && (
            <>
              <Tooltip content="Helpful">
                <button className="p-1.5 rounded-md bg-white border border-gray-100 shadow-sm text-gray-400 hover:text-blue-600 hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all">
                  <ThumbsUp size={14} />
                </button>
              </Tooltip>
              <Tooltip content="Not Helpful">
                <button className="p-1.5 rounded-md bg-white border border-gray-100 shadow-sm text-gray-400 hover:text-red-600 hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all">
                  <ThumbsDown size={14} />
                </button>
              </Tooltip>
            </>
          )}
          
          <Tooltip content={isCopied ? "Copied!" : "Copy"}>
            <button onClick={handleCopy} className="p-1.5 rounded-md bg-white border border-gray-100 shadow-sm text-gray-400 hover:text-gray-700 hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all">
              {isCopied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
            </button>
          </Tooltip>
          
          {isBot && onReplay && trace && (
            <Tooltip content="Replay Pipeline">
              <button onClick={onReplay} className="p-1.5 rounded-md bg-white border border-emerald-100 shadow-sm text-emerald-500 hover:text-emerald-700 hover:bg-emerald-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all ml-1">
                <RefreshCw size={14} />
              </button>
            </Tooltip>
          )}
        </div>
      </div>

      {/* User Avatar */}
      {!isBot && (
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 shadow-sm flex items-center justify-center text-gray-500 dark:text-gray-400 mt-1 z-10">
          <User size={18} />
        </div>
      )}
    </motion.div>
  );
};

