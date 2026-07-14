import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface RefreshDialogProps {
  isOpen: boolean;
  onConfirmClearChat: () => void;
  onConfirmClearBoth: () => void;
  onCancel: () => void;
}

export const RefreshDialog: React.FC<RefreshDialogProps> = ({ isOpen, onConfirmClearChat, onConfirmClearBoth, onCancel }) => {
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
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={onConfirmClearChat}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
                >
                  Clear Chat Only
                </button>
                <button
                  onClick={onConfirmClearBoth}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors shadow-sm"
                >
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
