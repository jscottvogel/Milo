"use client";

import { CheckCircle2, XCircle, AlertTriangle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

const PENDING = [
  { id: "a1", title: "Approve SOW for Cloud Migration", program: "Alpha Initiative", requestor: "Jane Doe", date: "2 hours ago", urgency: "high" },
  { id: "a2", title: "Q3 Vendor Budget Adjustment", program: "Beta Expansion", requestor: "Finance Team", date: "Yesterday", urgency: "medium" },
  { id: "a3", title: "Milo drafted: Client Status Update", program: "Gamma Integration", requestor: "Milo AI", date: "3 days ago", urgency: "low" },
];

const HISTORY = [
  { id: "h1", title: "Approve Architecture Design", program: "Alpha Initiative", requestor: "Eng Team", date: "May 1", status: "approved", actor: "You" },
  { id: "h2", title: "Extend Deadline by 2 weeks", program: "Beta Expansion", requestor: "John Smith", date: "Apr 28", status: "rejected", actor: "You" },
];

export default function ApprovalsQueue() {
  const [pending, setPending] = useState(PENDING);
  const [history, setHistory] = useState(HISTORY);

  const handleAction = (id: string, action: 'approved' | 'rejected') => {
    const item = pending.find(i => i.id === id);
    if (item) {
      setPending(pending.filter(i => i.id !== id));
      setHistory([{ ...item, status: action, actor: "You" }, ...history]);
      // In reality, this would trigger an API call to the approval workflow engine which sends a Nylas email
    }
  };

  return (
    <div className="p-6 h-full flex flex-col gap-8 overflow-y-auto custom-scrollbar">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Approvals Queue</h1>
        <p className="text-muted-foreground">Review and act on pending requests across all your programs.</p>
      </div>

      {/* Pending */}
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Clock className="w-5 h-5 text-amber-500" />
          Pending Action ({pending.length})
        </h2>
        
        {pending.length === 0 ? (
          <div className="bg-[#111115] border border-dashed border-white/10 rounded-xl p-8 flex flex-col items-center justify-center text-muted-foreground">
            <CheckCircle2 className="w-12 h-12 mb-4 text-white/10" />
            <p>You're all caught up!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {pending.map(item => (
              <div key={item.id} className="bg-[#111115] border border-white/10 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 group hover:border-white/20 transition-colors">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-semibold text-white text-lg">{item.title}</h3>
                    {item.urgency === 'high' && (
                      <span className="flex items-center gap-1 text-[10px] uppercase font-bold tracking-wider text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                        <AlertTriangle className="w-3 h-3" />
                        Urgent
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
                    <span className="bg-white/5 px-2 py-0.5 rounded text-white/80">{item.program}</span>
                    <span>Requested by <span className="text-white/80">{item.requestor}</span></span>
                    <span>{item.date}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 shrink-0">
                  <button 
                    onClick={() => handleAction(item.id, 'rejected')}
                    className="px-4 py-2 bg-white/5 hover:bg-red-500/20 text-white hover:text-red-400 rounded-lg text-sm font-medium transition-colors border border-transparent hover:border-red-500/30 flex items-center gap-2"
                  >
                    <XCircle className="w-4 h-4" />
                    Reject
                  </button>
                  <button 
                    onClick={() => handleAction(item.id, 'approved')}
                    className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* History */}
      <div className="flex flex-col gap-4 mt-8">
        <h2 className="text-lg font-semibold text-white text-muted-foreground">Recent History</h2>
        <div className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#0a0a0c] border-b border-white/10 text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-6 py-4 font-medium">Request</th>
                <th className="px-6 py-4 font-medium">Program</th>
                <th className="px-6 py-4 font-medium">Date</th>
                <th className="px-6 py-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-muted-foreground">
              {history.map(item => (
                <tr key={item.id} className="hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 text-white font-medium">{item.title}</td>
                  <td className="px-6 py-4">{item.program}</td>
                  <td className="px-6 py-4">{item.date}</td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "flex items-center gap-1.5 text-xs font-medium",
                      item.status === 'approved' ? "text-green-400" : "text-red-400"
                    )}>
                      {item.status === 'approved' ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                      <span className="capitalize">{item.status}</span>
                      <span className="text-muted-foreground ml-1 font-normal">by {item.actor}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
