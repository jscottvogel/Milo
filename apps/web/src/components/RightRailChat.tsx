"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, PanelRightClose } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';

import { Send, Loader2 } from 'lucide-react';
import { sendMiloMessage } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const Chat = ({ contextLabel }: { contextLabel: string }) => {
  const [messages, setMessages] = React.useState<Message[]>([{
    id: '1',
    role: 'assistant',
    content: `Hi, I'm Milo. How can I help you with ${contextLabel}?`
  }]);
  const [input, setInput] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // In a real integration, the response might be streamed or we might get a thread_id back
      // Using our generic placeholder apiClient for now
      const res = await sendMiloMessage(userMessage.content, contextLabel);
      
      const assistantMessage: Message = { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        content: res?.answer || res?.message || "I've received your request." 
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);
      const errorMessage: Message = { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        content: "Sorry, I'm having trouble connecting to my neural core right now." 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0a0c]">
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.map((msg) => (
          <div key={msg.id} className={cn("flex", msg.role === 'user' ? "justify-end" : "justify-start")}>
            <div className={cn(
              "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm",
              msg.role === 'user' 
                ? "bg-primary text-primary-foreground rounded-br-none" 
                : "bg-white/10 text-white rounded-bl-none border border-white/5"
            )}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white/10 border border-white/5 rounded-2xl rounded-bl-none px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
              <span className="text-xs text-muted-foreground">Milo is thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="p-4 bg-[#0f0f13] border-t border-white/10">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Milo anything..."
            className="w-full bg-white/5 border border-white/10 rounded-full pl-4 pr-12 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary transition-all placeholder:text-muted-foreground/50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-1.5 p-1.5 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 disabled:opacity-50 disabled:hover:bg-primary transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

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
              <Chat contextLabel={contextLabel} />
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
};
