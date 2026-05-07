import { useEffect, useState } from 'react';
import { Check, X, Clock, ShieldAlert, FileJson } from 'lucide-react';

interface Approval {
  id: string;
  tool_name: string;
  payload: any;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  expires_at: string;
}

export function Approvals() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchApprovals = async () => {
    try {
      const res = await fetch('http://localhost:8000/v1/approvals?status=pending', {
        headers: {
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
        }
      });
      if (res.ok) {
        const data = await res.json();
        setApprovals(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleDecision = async (id: string, decision: 'approve' | 'reject') => {
    // Optimistic update
    setApprovals(prev => prev.filter(a => a.id !== id));
    
    try {
      await fetch(`http://localhost:8000/v1/approvals/${id}/decide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
        },
        body: JSON.stringify({ decision })
      });
    } catch (e) {
      console.error(e);
      // Revert if failed (omitted for brevity)
    }
  };

  if (isLoading) {
    return <div className="flex h-full items-center justify-center text-muted-foreground z-10">Loading queue...</div>;
  }

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto p-8 z-10 overflow-y-auto scrollbar-hide">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <ShieldAlert className="text-primary" size={32} />
          Action Queue
        </h2>
        <p className="text-muted-foreground mt-2">Review and authorize pending agent actions requiring human-in-the-loop governance.</p>
      </div>

      {approvals.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 glass-card border-dashed p-12 text-center animate-fade-in">
          <Check className="w-16 h-16 text-muted-foreground/30 mb-4" />
          <h3 className="text-xl font-medium text-white">All caught up</h3>
          <p className="text-muted-foreground mt-2 max-w-sm">There are no pending actions requiring your authorization at this time.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {approvals.map((approval) => (
            <div key={approval.id} className="glass-card p-6 animate-slide-up flex flex-col md:flex-row gap-6 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-1 h-full bg-amber-500/50 group-hover:bg-amber-500 transition-colors" />
              
              <div className="flex-1 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="px-3 py-1 bg-surface border border-white/10 rounded-full text-xs font-mono text-primary flex items-center gap-2 shadow-sm">
                      <FileJson size={14} />
                      {approval.tool_name}
                    </span>
                    <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Clock size={14} />
                      Expires: {new Date(approval.expires_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                
                <div className="bg-black/50 border border-white/10 rounded-xl p-4 overflow-x-auto">
                  <pre className="text-sm font-mono text-gray-300">
                    {JSON.stringify(approval.payload, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="flex flex-row md:flex-col gap-3 justify-center md:min-w-[140px]">
                <button
                  onClick={() => handleDecision(approval.id, 'approve')}
                  className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white font-medium transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_20px_rgba(59,130,246,0.5)]"
                >
                  <Check size={18} />
                  Approve
                </button>
                <button
                  onClick={() => handleDecision(approval.id, 'reject')}
                  className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-surface hover:bg-white/10 border border-white/10 text-white font-medium transition-all"
                >
                  <X size={18} />
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
