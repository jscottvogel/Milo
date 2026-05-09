import { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, XCircle, RefreshCw, Play } from 'lucide-react';
import clsx from 'clsx';

interface EntityStatus {
  type: string;
  name: string;
  status: 'pending' | 'running' | 'retrying' | 'created' | 'failed';
  attempt_count: number;
  error: string | null;
  id?: string;
}

interface HydrationStatus {
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_attempted: number;
  total_created: number;
  total_failed: number;
  error?: string;
  entities: EntityStatus[];
}

export function HydrationPanel({ runId, onClose }: { runId: string, onClose?: () => void }) {
  const [data, setData] = useState<HydrationStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  const fetchStatus = async () => {
    try {
      const RAW_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const API_URL = RAW_API_URL.endsWith('/') ? RAW_API_URL.slice(0, -1) : RAW_API_URL;
      
      const res = await fetch(`${API_URL}/v1/work_items/hydration/${runId}/status`, {
        headers: {
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
        }
      });
      if (res.ok) {
        const json = await res.json();
        setData(json);
        if (json.status === 'completed' || json.status === 'failed') {
          setIsPolling(false);
        }
      }
    } catch (e) {
      console.error("Failed to fetch hydration status", e);
    }
  };

  useEffect(() => {
    if (!isPolling) return;
    
    // Initial fetch
    fetchStatus();
    
    // Poll every 2 seconds
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [runId, isPolling]);

  const handleRetryFailed = async () => {
    // This is a simplified retry that re-triggers the whole execution.
    // Since the backend uses idempotent upserts, it will cleanly skip already created ones!
    setIsPolling(true);
    try {
      const RAW_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const API_URL = RAW_API_URL.endsWith('/') ? RAW_API_URL.slice(0, -1) : RAW_API_URL;
      await fetch(`${API_URL}/v1/work_items/hydration/${runId}/execute`, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
        }
      });
    } catch (e) {
      console.error(e);
    }
  };

  if (!data) {
    return (
      <div className="p-6 glass-card rounded-xl animate-pulse flex items-center justify-center">
        <Loader2 className="animate-spin text-primary mr-3" />
        <span className="text-muted-foreground">Initializing Hydration Engine...</span>
      </div>
    );
  }

  const progressPct = data.total_attempted > 0 ? (data.total_created / data.total_attempted) * 100 : 0;

  return (
    <div className="glass-card rounded-xl overflow-hidden shadow-2xl border border-white/10 w-full max-w-2xl animate-fade-in-up">
      <div className="p-5 border-b border-white/10 bg-surface/50 flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-lg flex items-center gap-2">
            Program Hydration
            {data.status === 'running' && <span className="flex h-2 w-2 relative ml-1"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span></span>}
          </h3>
          <p className="text-xs text-muted-foreground mt-1">Run ID: {runId}</p>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-muted-foreground hover:text-white transition-colors">
            Close
          </button>
        )}
      </div>

      <div className="p-5 space-y-6">
        {/* Progress Summary */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium text-white">{data.total_created} / {data.total_attempted || '?'} Created</span>
          </div>
          <div className="h-2 w-full bg-black/40 rounded-full overflow-hidden flex">
            <div 
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500 ease-out" 
              style={{ width: `${progressPct}%` }}
            />
          </div>
          
          <div className="flex justify-between mt-3 text-xs">
            <span className="flex items-center text-green-400 gap-1"><CheckCircle2 size={14}/> {data.total_created} Created</span>
            <span className="flex items-center text-red-400 gap-1"><XCircle size={14}/> {data.total_failed} Failed</span>
          </div>
        </div>

        {/* Tree List */}
        <div className="max-h-64 overflow-y-auto pr-2 space-y-2 scrollbar-thin">
          {data.entities.length === 0 && data.status !== 'pending' && (
            <p className="text-muted-foreground text-sm italic text-center py-4">No entities found to hydrate.</p>
          )}
          {data.entities.map((entity, idx) => (
            <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-surface/30 border border-white/5 hover:bg-surface/50 transition-colors">
              <div className="flex items-center gap-3 overflow-hidden">
                <span className={clsx(
                  "px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded border",
                  entity.type === 'objective' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                  entity.type === 'outcome' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                  entity.type === 'key_result' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                  entity.type === 'project' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  entity.type === 'milestone' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                  'bg-gray-500/10 text-gray-400 border-gray-500/20'
                )}>
                  {entity.type.replace('_', ' ')}
                </span>
                <span className="text-sm font-medium truncate text-gray-200" title={entity.name}>
                  {entity.name}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {entity.status === 'created' && <CheckCircle2 size={16} className="text-green-500" />}
                {entity.status === 'failed' && <XCircle size={16} className="text-red-500" />}
                {(entity.status === 'running' || entity.status === 'retrying') && <Loader2 size={16} className="text-primary animate-spin" />}
                {entity.status === 'pending' && <div className="w-2 h-2 rounded-full bg-gray-600 mr-1" />}
              </div>
            </div>
          ))}
        </div>

        {/* Action Bar */}
        {(data.status === 'completed' || data.status === 'failed') && (
          <div className="flex justify-end gap-3 pt-4 border-t border-white/10 mt-4">
            {data.total_failed > 0 && (
              <button 
                onClick={handleRetryFailed}
                className="flex items-center gap-2 px-4 py-2 bg-surface hover:bg-white/5 border border-white/10 rounded-lg text-sm transition-colors"
              >
                <RefreshCw size={14} className="text-primary" /> Retry Failed
              </button>
            )}
            <button 
                onClick={handleRetryFailed}
                className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm shadow-lg shadow-primary/25 transition-colors"
              >
                <Play size={14} /> Re-hydrate from Source
              </button>
          </div>
        )}
      </div>
    </div>
  );
}
