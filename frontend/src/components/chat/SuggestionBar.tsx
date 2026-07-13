import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Hand, Building, Clock, FileText, CalendarOff, PhoneCall, Briefcase, HelpCircle } from 'lucide-react';

interface SuggestionBarProps {
  isVisible: boolean;
  onSuggestionClick: (suggestion: string) => void;
}

const SUGGESTIONS = [
  { text: "Hello", icon: Hand },
  { text: "Company Details", icon: Building },
  { text: "Working Hours", icon: Clock },
  { text: "HR Policy", icon: FileText },
  { text: "Leave Policy", icon: CalendarOff },
  { text: "Contact HR", icon: PhoneCall },
  { text: "Careers", icon: Briefcase },
];

export const SuggestionBar: React.FC<SuggestionBarProps> = ({ isVisible, onSuggestionClick }) => {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="flex overflow-x-auto no-scrollbar gap-2 mb-3 pb-1"
        >
          {SUGGESTIONS.map((s, idx) => {
            const Icon = s.icon;
            return (
              <motion.button
                key={s.text}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                type="button"
                onPointerDown={(e) => {
                  e.preventDefault();
                  onSuggestionClick(s.text);
                }}
                className="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 bg-[var(--color-cards)] hover:bg-blue-50 dark:hover:bg-slate-800 border border-[var(--color-border)] hover:border-blue-200 dark:hover:border-blue-500/50 text-gray-600 dark:text-gray-300 hover:text-blue-700 dark:hover:text-blue-400 rounded-full text-[11px] sm:text-xs font-medium transition-colors shadow-sm cursor-pointer"
              >
                <Icon size={12} className={idx === 0 ? "text-amber-500" : "text-blue-500"} />
                {s.text}
              </motion.button>
            );
          })}
        </motion.div>
      )}
    </AnimatePresence>
  );
};
