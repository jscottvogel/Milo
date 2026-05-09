import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Loader2, Paperclip, X } from 'lucide-react';
import clsx from 'clsx';
import { HydrationPanel } from '../components/HydrationPanel';
import { apiFetch, getToken } from '../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello! I am Milo. How can I help you manage your programs today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(prev => [...prev, ...Array.from(e.target.files!)]);
    }
    // Clear input so same file can be selected again if removed
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && selectedFiles.length === 0) || isLoading) return;

    setIsLoading(true);
    let finalContent = input.trim();
    let uploadedPaths: string[] = [];

    try {
      if (selectedFiles.length > 0) {
        // Duplicate detection
        for (const file of selectedFiles) {
          const checkData = await apiFetch<any>('/v1/files/check-duplicate', {
            method: 'POST',
            body: JSON.stringify({ filename: file.name })
          });
          if (checkData.exists) {
            if (!window.confirm(`The file "${file.name}" has already been uploaded. Overwrite and re-ingest?`)) {
              setIsLoading(false);
              return;
            }
          }
        }

        // Upload
        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('files', file));

        const uploadData = await apiFetch<any>('/v1/files/upload', {
          method: 'POST',
          body: formData
        });

        uploadedPaths = uploadData.paths || [];

        const systemPrompt = `\n\n[SYSTEM] I have uploaded the following files: ${uploadedPaths.join(", ")}. Please parse them via file.read, extract document type, key facts, decisions, architecture components, and prompts, write them to memory, and give me a summary of what you extracted.`;
        finalContent += systemPrompt;
        setSelectedFiles([]);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setIsLoading(false);
      return;
    }

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: finalContent };
    setMessages(prev => [...prev, { ...userMessage, content: input.trim() || `Uploaded ${selectedFiles.length} file(s)` }]);
    setInput('');

    // Mock Thread ID for PoC (Must be a valid UUID)
    const threadId = '123e4567-e89b-12d3-a456-426614174000';
    
    try {
      const RAW_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const API_URL = RAW_API_URL.endsWith('/') ? RAW_API_URL.slice(0, -1) : RAW_API_URL;
      const response = await fetch(`${API_URL}/v1/threads/${threadId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ content: userMessage.content })
      });

      if (!response.body) throw new Error('No readable stream');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      const assistantMessageId = Date.now().toString();
      setMessages(prev => [...prev, { id: assistantMessageId, role: 'assistant', content: '', isStreaming: true }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'token') {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: msg.content + data.content }
                    : msg
                ));
              } else if (data.type === 'tool_start') {
                 setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: msg.content + `\n\n> ⚡ Using tool: \`${data.tool_name}\`\n\n` }
                    : msg
                ));
              } else if (data.type === 'approval_request') {
                 setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: msg.content + `\n\n> 🛡️ **Approval Required:** Please go to the [Approvals](/approvals) tab to approve the \`${data.tool_name}\` action.\n\n` }
                    : msg
                ));
              } else if (data.type === 'error') {
                 setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: msg.content + `\n\n> ❌ **Error:** ${data.message}\n\n` }
                    : msg
                ));
              } else if (data.type === 'tool_result') {
                 setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: msg.content + `\n\n> ✅ **Tool \`${data.tool_name}\` Complete**\n\n` }
                    : msg
                ));
              }
            } catch (e) {
              console.error('Error parsing SSE json', e);
            }
          }
        }
      }
      
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
      ));
      
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'assistant', 
        content: 'Sorry, I encountered an error communicating with the server.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full mx-auto p-4 z-10 relative">
      <div className="flex-1 overflow-y-auto scrollbar-hide py-4 space-y-6 px-2">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={clsx(
              "flex gap-3 max-w-[95%] animate-fade-in",
              message.role === 'user' ? "ml-auto flex-row-reverse" : ""
            )}
          >
            <div className={clsx(
              "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-lg",
              message.role === 'user' 
                ? "bg-gradient-to-br from-indigo-500 to-purple-600" 
                : "bg-surface border border-white/10"
            )}>
              {message.role === 'user' ? <User size={16} /> : <Bot size={16} className="text-primary" />}
            </div>
            
            <div className={clsx(
              "px-5 py-3.5 rounded-2xl shadow-sm",
              message.role === 'user'
                ? "bg-primary text-white rounded-tr-sm"
                : "glass-card text-gray-100 rounded-tl-sm w-full"
            )}>
              {message.role === 'user' ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <div className="prose prose-invert prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 max-w-none">
                  <ReactMarkdown>{message.content.replace(/\[HYDRATION_RUN:[^\]]+\]/, '')}</ReactMarkdown>
                  
                  {message.content.includes('[HYDRATION_RUN:') && (
                    <div className="mt-4 mb-2">
                      {(() => {
                        const match = message.content.match(/\[HYDRATION_RUN:([^\]]+)\]/);
                        if (match) {
                          return <HydrationPanel runId={match[1]} />;
                        }
                        return null;
                      })()}
                    </div>
                  )}

                  {message.isStreaming && (
                    <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse align-middle"></span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="mt-4">
        {selectedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2 px-2">
            {selectedFiles.map((f, idx) => (
              <div key={idx} className="flex items-center gap-1 bg-surface/80 backdrop-blur text-xs px-2 py-1 rounded-full border border-white/10">
                <Paperclip size={12} className="text-primary" />
                <span className="truncate max-w-[150px]">{f.name}</span>
                <button type="button" onClick={() => removeFile(idx)} className="text-muted-foreground hover:text-white ml-1">
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
        <form 
          onSubmit={handleSubmit} 
          className="relative flex items-center bg-surface/80 backdrop-blur-xl border border-white/10 rounded-full shadow-2xl p-1.5 focus-within:border-primary/50 transition-colors"
        >
          <input
            type="file"
            multiple
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx,.txt,.md,.xlsx,.csv,.pptx,.json,.yaml,.html"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground hover:text-white hover:bg-white/5 transition-all"
          >
            <Paperclip size={20} />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message Milo or attach files..."
            className="flex-1 bg-transparent border-none outline-none px-2 py-3 text-white placeholder-muted-foreground"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            disabled={(!input.trim() && selectedFiles.length === 0) || isLoading}
            className="flex items-center justify-center w-12 h-12 rounded-full bg-primary text-white hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} className="ml-1" />}
          </button>
        </form>
        <p className="text-center text-xs text-muted-foreground mt-3">Milo AI can make mistakes. Consider verifying important information.</p>
      </div>
    </div>
  );
}
