import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface RefreshDialogProps {
  isOpen: boolean;
  onConfirmClearChat: () => Promise<void> | void;
  onConfirmClearBoth: () => Promise<void> | void;
  onCancel: () => void;
}

export const RefreshDialog: React.FC<RefreshDialogProps> = ({ isOpen, onConfirmClearChat, onConfirmClearBoth, onCancel }) => {
  const [isClearingChat, setIsClearingChat] = useState(false);
  const [isClearingBoth, setIsClearingBoth] = useState(false);

  const handleClearChat = async () => {
    setIsClearingChat(true);
    try {
      await onConfirmClearChat();
    } finally {
      setIsClearingChat(false);
    }
  };

  const handleClearBoth = async () => {
    setIsClearingBoth(true);
    try {
      await onConfirmClearBoth();
    } finally {
      setIsClearingBoth(false);
    }
  };

  const isAnyLoading = isClearingChat || isClearingBoth;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden"
          >
            <div className="p-5">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Clear Conversation?</h3>
              <p className="text-sm text-gray-600 mb-6">
                Do you also want to clear remembered information?
              </p>
              <div className="flex flex-col sm:flex-row justify-end gap-3">
                <button
                  onClick={onCancel}
                  disabled={isAnyLoading}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleClearChat}
                  disabled={isAnyLoading}
                  className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-70 min-w-[120px]"
                >
                  {isClearingChat && <Loader2 size={16} className="animate-spin" />}
                  Clear Chat Only
                </button>
                <button
                  onClick={handleClearBoth}
                  disabled={isAnyLoading}
                  className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors shadow-sm disabled:opacity-70 min-w-[150px]"
                >
                  {isClearingBoth && <Loader2 size={16} className="animate-spin" />}
                  Clear Chat + Memory
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
