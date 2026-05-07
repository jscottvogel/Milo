import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import clsx from 'clsx';

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Mock Thread ID for PoC
    const threadId = 'thread-123';
    
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/v1/threads/${threadId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
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
    <div className="flex flex-col h-full w-full max-w-4xl mx-auto p-4 z-10 relative">
      <div className="flex-1 overflow-y-auto scrollbar-hide py-4 space-y-6 px-2">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={clsx(
              "flex gap-4 max-w-[85%] animate-fade-in",
              message.role === 'user' ? "ml-auto flex-row-reverse" : ""
            )}
          >
            <div className={clsx(
              "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-lg",
              message.role === 'user' 
                ? "bg-gradient-to-br from-indigo-500 to-purple-600" 
                : "bg-surface border border-white/10"
            )}>
              {message.role === 'user' ? <User size={20} /> : <Bot size={20} className="text-primary" />}
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
                  <ReactMarkdown>{message.content || '...'}</ReactMarkdown>
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
        <form 
          onSubmit={handleSubmit} 
          className="relative flex items-center bg-surface/80 backdrop-blur-xl border border-white/10 rounded-full shadow-2xl p-1.5 focus-within:border-primary/50 transition-colors"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message Milo..."
            className="flex-1 bg-transparent border-none outline-none px-4 py-3 text-white placeholder-muted-foreground"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isLoading}
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
