import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, PanelRightClose } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Chat } from '../pages/Chat'; // We will use the existing Chat component but style it for the rail

export const RightRailChat: React.FC = () => {
  const { isRightRailOpen, toggleRightRail, breadcrumbContext } = useAppStore();

  const contextLabel = breadcrumbContext.length > 0 
    ? breadcrumbContext[breadcrumbContext.length - 1].label 
    : 'Home';

  return (
    <>
      {/* Floating Action Button for Mobile/Collapsed State */}
      <AnimatePresence>
        {!isRightRailOpen && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={toggleRightRail}
            className="fixed bottom-6 right-6 z-50 bg-primary text-primary-foreground p-4 rounded-full shadow-lg hover:bg-primary/90 flex items-center gap-2"
          >
            <MessageSquare className="w-6 h-6" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Right Rail Panel */}
      <AnimatePresence>
        {isRightRailOpen && (
          <motion.aside
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 right-0 z-40 w-full sm:w-[400px] border-l border-border bg-background shadow-2xl flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <h3 className="font-semibold text-sm">Milo Assistant</h3>
                </div>
                <div className="text-xs text-muted-foreground mt-1 bg-white/5 px-2 py-1 rounded-md max-w-[280px] truncate">
                  Context: <strong>{contextLabel}</strong>
                </div>
              </div>
              <button 
                onClick={toggleRightRail}
                className="p-2 hover:bg-white/10 rounded-md transition-colors"
              >
                <PanelRightClose className="w-5 h-5 text-muted-foreground" />
              </button>
            </div>

            {/* Chat Content */}
            <div className="flex-1 overflow-hidden relative">
              <Chat />
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
};
