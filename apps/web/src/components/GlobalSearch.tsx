import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, FileText, Mail, CheckCircle, Package } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export const GlobalSearch: React.FC = () => {
  const { isSearchOpen, setSearchOpen } = useAppStore();
  const [query, setQuery] = useState('');

  // Handle Cmd+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (e.key === 'Escape' && isSearchOpen) {
        setSearchOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSearchOpen, setSearchOpen]);

  // Mock search results
  const results = query.length > 2 ? [
    { type: 'program', title: 'Alpha Initiative', icon: Package },
    { type: 'approval', title: 'Q3 Budget Request', icon: CheckCircle },
    { type: 'email', title: 'Fwd: Project timeline update', icon: Mail },
    { type: 'decision', title: 'Vendor selection finalized', icon: FileText },
  ] : [];

  return (
    <AnimatePresence>
      {isSearchOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4 sm:px-0">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSearchOpen(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
          />
          
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="relative w-full max-w-xl bg-[#111115] border border-border rounded-xl shadow-2xl overflow-hidden flex flex-col"
          >
            <div className="flex items-center px-4 py-3 border-b border-white/10">
              <Search className="w-5 h-5 text-muted-foreground mr-3" />
              <input
                autoFocus
                type="text"
                placeholder="Search programs, emails, decisions..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-muted-foreground"
              />
              <div className="flex items-center gap-1 text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded">
                <span>esc</span>
              </div>
            </div>

            {query.length > 0 && (
              <div className="max-h-[60vh] overflow-y-auto p-2">
                {results.length > 0 ? (
                  <div className="space-y-1">
                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Results
                    </div>
                    {results.map((r, i) => (
                      <button
                        key={i}
                        className="w-full flex items-center px-3 py-3 rounded-lg hover:bg-white/10 transition-colors text-left group"
                        onClick={() => setSearchOpen(false)}
                      >
                        <r.icon className="w-4 h-4 mr-3 text-muted-foreground group-hover:text-primary" />
                        <span className="flex-1 text-sm">{r.title}</span>
                        <span className="text-xs text-muted-foreground capitalize bg-white/5 px-2 py-0.5 rounded">
                          {r.type}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center text-muted-foreground">
                    <p>No results found for "{query}"</p>
                  </div>
                )}
              </div>
            )}
            
            {query.length === 0 && (
              <div className="p-4 flex gap-2 overflow-x-auto text-xs">
                <span className="whitespace-nowrap px-3 py-1.5 rounded-full bg-white/5 text-muted-foreground hover:bg-white/10 hover:text-white cursor-pointer transition-colors border border-white/5">
                  Try "Q3 Goals"
                </span>
                <span className="whitespace-nowrap px-3 py-1.5 rounded-full bg-white/5 text-muted-foreground hover:bg-white/10 hover:text-white cursor-pointer transition-colors border border-white/5">
                  Try "Pending Approvals"
                </span>
                <span className="whitespace-nowrap px-3 py-1.5 rounded-full bg-white/5 text-muted-foreground hover:bg-white/10 hover:text-white cursor-pointer transition-colors border border-white/5">
                  Try "Recent Emails"
                </span>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
