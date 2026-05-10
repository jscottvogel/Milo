"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, PanelRightClose } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';

import { Send, Loader2, Plus, X, File as FileIcon, FileText } from 'lucide-react';
import { sendMiloMessage, checkDuplicateFile, uploadFiles } from '@/lib/api';

const ALLOWED_EXTS = ['.pdf', '.docx', '.txt', '.md', '.xlsx', '.csv', '.pptx', '.json', '.yaml', '.html'];

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
  const [attachedFiles, setAttachedFiles] = React.useState<File[]>([]);
  const [isDragging, setIsDragging] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const validateFile = (file: File): string | null => {
    if (file.size > 25 * 1024 * 1024) {
      return `File ${file.name} exceeds 25MB limit.`;
    }
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      return `Format ${ext} is not supported. Supported: ${ALLOWED_EXTS.join(', ')}`;
    }
    return null;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      const validFiles: File[] = [];
      for (const f of newFiles) {
        const err = validateFile(f);
        if (err) {
          setMessages(prev => [...prev, { id: Date.now().toString() + Math.random(), role: 'assistant', content: err }]);
        } else {
          validFiles.push(f);
        }
      }
      setAttachedFiles(prev => [...prev, ...validFiles]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if ((!input.trim() && attachedFiles.length === 0) || isLoading) return;

    let finalInput = input;
    let uploadedPaths: string[] = [];

    setIsLoading(true);

    if (attachedFiles.length > 0) {
      try {
        for (const file of attachedFiles) {
          const res = await checkDuplicateFile(file.name);
          if (res.exists) {
            const overwrite = window.confirm(`File '${file.name}' already exists in memory. Overwrite?`);
            if (!overwrite) {
              setIsLoading(false);
              return;
            }
          }
        }
        
        const uploadRes = await uploadFiles(attachedFiles);
        uploadedPaths = uploadRes.paths || [];

        const instruction = `[User attached ${attachedFiles.length} files]
Paths: ${uploadedPaths.join(', ')}

Instructions for Milo:
The user has securely uploaded these files. Please sequentially:
1. Parse each file using the \`file.read\` tool.
2. Analyze the content: extract document type, key facts, decisions, architecture components, stakeholders, and dates.
3. Write structured episodic memory entries via \`memory.write\`: one summary entry per document, and individual entries for key decisions/components. Tag with metadata: { source_file, upload_date, document_type }.
4. Respond in chat confirming: file name, size, storage path, document type, number of memory entries written, and a bullet summary.

User message: ${input}`;

        finalInput = instruction;

      } catch (err: any) {
        console.error(err);
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: `Upload failed: ${err.message}` }]);
        setIsLoading(false);
        return;
      }
    }

    const displayContent = input || `[Attached ${attachedFiles.length} file${attachedFiles.length > 1 ? 's' : ''}]`;
    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: displayContent };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setAttachedFiles([]);

    try {
      // In a real integration, the response might be streamed or we might get a thread_id back
      // Using our generic placeholder apiClient for now
      const res = await sendMiloMessage(finalInput, contextLabel);
      
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
    <div 
      className={cn("flex flex-col h-full bg-[#0a0a0c] transition-all", isDragging && "bg-white/5 border-2 border-primary border-dashed")}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const newFiles = Array.from(e.dataTransfer.files);
        const validFiles: File[] = [];
        for (const f of newFiles) {
          const err = validateFile(f);
          if (err) {
            setMessages(prev => [...prev, { id: Date.now().toString() + Math.random(), role: 'assistant', content: err }]);
          } else {
            validFiles.push(f);
          }
        }
        setAttachedFiles(prev => [...prev, ...validFiles]);
      }}
    >
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
      
      <div className="p-4 bg-[#0f0f13] border-t border-white/10 flex flex-col gap-2">
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {attachedFiles.map((f, i) => (
              <div key={i} className="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-xs text-white border border-white/10">
                <FileText className="w-3 h-3 text-primary" />
                <span className="truncate max-w-[150px]">{f.name}</span>
                <span className="text-muted-foreground">{(f.size / 1024 / 1024).toFixed(1)}MB</span>
                <button type="button" onClick={() => removeFile(i)} className="text-muted-foreground hover:text-white transition-colors">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
        <form onSubmit={handleSend} className="relative flex items-center">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="absolute left-1.5 p-1.5 text-muted-foreground hover:text-white transition-colors"
            title="Attach files"
          >
            <Plus className="w-4 h-4" />
          </button>
          <input
            type="file"
            multiple
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileSelect}
            accept={ALLOWED_EXTS.join(',')}
          />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Milo anything or attach files..."
            className="w-full bg-white/5 border border-white/10 rounded-full pl-10 pr-12 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary transition-all placeholder:text-muted-foreground/50"
          />
          <button
            type="submit"
            disabled={(!input.trim() && attachedFiles.length === 0) || isLoading}
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
