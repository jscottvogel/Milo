"use client";

import { useState } from "react";
import { Mail, Search, MessageSquare, Bot, ArrowRight, CornerUpLeft } from "lucide-react";
import { cn } from "@/lib/utils";

const DUMMY_EMAILS = [
  { id: "e1", subject: "RE: Phase 2 SOW Approval", sender: "Jane Executive", snippet: "I've reviewed the attached SOW. Looks good, but...", date: "10:30 AM", unread: true, miloDraft: "Thanks Jane, I will update the timeline section today and resend for signature." },
  { id: "e2", subject: "Vendor meeting notes", sender: "Bob Director", snippet: "Here are the notes from yesterday's sync with the DB vendor.", date: "Yesterday", unread: false, miloDraft: null },
  { id: "e3", subject: "Fwd: Budget variance alert", sender: "Finance Team", snippet: "We noticed a 5% variance in the Q2 budget.", date: "May 5", unread: true, miloDraft: "Hi Team, the variance is due to the expedited shipping for the new servers. See attached invoice." },
];

export default function Inbox() {
  const [selectedId, setSelectedId] = useState<string | null>(DUMMY_EMAILS[0].id);
  const selected = DUMMY_EMAILS.find(e => e.id === selectedId);

  return (
    <div className="flex gap-6 h-[calc(100vh-160px)]">
      
      {/* Email List */}
      <div className="w-1/3 min-w-[300px] flex flex-col gap-4 border-r border-white/10 pr-6">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Mail className="w-5 h-5 text-purple-500" />
            Program Inbox
          </h2>
          <span className="bg-primary/20 text-primary text-xs py-0.5 px-2 rounded-full border border-primary/30">
            {DUMMY_EMAILS.filter(e => e.unread).length} unread
          </span>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Search emails..." 
            className="w-full bg-[#111115] border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
          />
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-2">
          {DUMMY_EMAILS.map(email => (
            <button
              key={email.id}
              onClick={() => setSelectedId(email.id)}
              className={cn(
                "p-4 rounded-xl text-left transition-colors border",
                selectedId === email.id 
                  ? "bg-primary/10 border-primary/30" 
                  : "bg-[#111115] border-white/5 hover:bg-white/5 hover:border-white/10"
              )}
            >
              <div className="flex justify-between items-start mb-1">
                <span className={cn("font-medium text-sm truncate pr-2", email.unread ? "text-white" : "text-muted-foreground")}>
                  {email.sender}
                </span>
                <span className="text-xs text-muted-foreground shrink-0">{email.date}</span>
              </div>
              <div className={cn("text-sm mb-1 truncate", email.unread ? "text-white font-medium" : "text-white/80")}>
                {email.subject}
              </div>
              <div className="text-xs text-muted-foreground line-clamp-2">
                {email.snippet}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Thread View */}
      {selected ? (
        <div className="flex-1 flex flex-col bg-[#111115] border border-white/10 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-white/10 bg-[#0a0a0c]">
            <h3 className="text-xl font-bold text-white mb-4">{selected.subject}</h3>
            <div className="flex justify-between items-center text-sm">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg border border-white/10">
                  {selected.sender[0]}
                </div>
                <div>
                  <div className="font-medium text-white">{selected.sender}</div>
                  <div className="text-muted-foreground text-xs">to me, Program Team</div>
                </div>
              </div>
              <div className="text-muted-foreground text-xs">{selected.date}</div>
            </div>
          </div>
          
          <div className="flex-1 p-6 overflow-y-auto custom-scrollbar text-sm text-white/80 leading-relaxed">
            <p>{selected.snippet} (Imagine full email body here...)</p>
          </div>

          {/* Milo's Suggested Reply */}
          {selected.miloDraft && (
            <div className="p-4 border-t border-white/10 bg-indigo-500/5">
              <div className="flex items-center gap-2 text-indigo-400 font-medium text-sm mb-3">
                <Bot className="w-4 h-4" />
                Milo's Suggested Reply
              </div>
              <div className="bg-[#0a0a0c] border border-indigo-500/20 rounded-lg p-4 text-sm text-white/90 mb-4">
                {selected.miloDraft}
              </div>
              <div className="flex gap-3">
                <button className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <ArrowRight className="w-4 h-4" />
                  Approve & Send
                </button>
                <button className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg text-sm font-medium transition-colors border border-white/10 flex items-center gap-2">
                  <CornerUpLeft className="w-4 h-4" />
                  Edit
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-muted-foreground border border-dashed border-white/10 rounded-xl">
          Select an email to view
        </div>
      )}

    </div>
  );
}
