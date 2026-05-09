import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, useAnimation } from 'framer-motion';
import { useAppStore } from '../store/useAppStore';
import clsx from 'clsx';
import { Check, X, ArrowRight, Clock, User, FileText, Filter, CheckCircle } from 'lucide-react';
import { apiFetch } from '../api/client';

interface Approval {
  id: string;
  title: string;
  status: string;
  due_by?: string;
  requested_by?: string;
  description?: string;
  options?: string[];
}

export const Approvals: React.FC = () => {
  const { setBreadcrumbContext, setPendingApprovalsCount, decrementPendingApprovals } = useAppStore();
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'approved' | 'rejected' | 'delegated'>('pending');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    setBreadcrumbContext([{ label: 'Approvals Queue', path: '/approvals' }]);
  }, [setBreadcrumbContext]);

  const fetchApprovals = async () => {
    try {
      // In a real app, you'd attach the tenant JWT auth token here
      const data = await apiFetch<any>('/v1/approvals'); 
      const rawItems = Array.isArray(data) ? data : (data.approvals || []);
      const items = rawItems.map((item: any) => ({
        id: item.id,
        title: `Action: ${item.tool_name}`,
        status: item.status,
        due_by: item.expires_at,
        requested_by: 'Milo Agent',
        description: JSON.stringify(item.payload, null, 2),
        options: ['approve', 'reject']
      }));
      
      // Update store with pending count
      const pendingCount = items.filter((a: Approval) => a.status === 'pending').length;
      setPendingApprovalsCount(pendingCount);
      
      setApprovals(items);
    } catch (err) {
      console.warn('Failed to fetch approvals from API, using dummy data', err);
      // Fallback dummy data for UI demonstration
      const dummyData: Approval[] = [
        {
          id: '1',
          title: 'Q3 Marketing Budget Increase',
          status: 'pending',
          requested_by: 'Sarah Jenkins',
          due_by: new Date(Date.now() + 86400000).toISOString(),
          description: 'Requesting an additional $5k to run a targeted ad campaign for the Enterprise tier launch.',
          options: ['approve', 'reject', 'delegate', 'defer']
        },
        {
          id: '2',
          title: 'Vendor Contract: Acme Corp',
          status: 'pending',
          requested_by: 'Alex Chen',
          due_by: new Date(Date.now() + 3600000 * 2).toISOString(), // Due in 2 hours
          description: 'Legal has reviewed the final redlines. We need executive approval before signing.',
          options: ['approve', 'reject']
        }
      ];
      setApprovals(dummyData);
      setPendingApprovalsCount(dummyData.filter((a: Approval) => a.status === 'pending').length);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
    const interval = setInterval(fetchApprovals, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (approvalId: string, decision: string) => {
    // Optimistic UI update
    setApprovals(prev => prev.map(a => a.id === approvalId ? { ...a, status: decision } : a));
    if (activeTab === 'pending') {
      decrementPendingApprovals();
    }

    try {
      await apiFetch(`/v1/approvals/${approvalId}/decide`, {
        method: 'POST',
        body: JSON.stringify({
          decision,
          notes: '', // Can be extended to open a modal for notes if needed
          decided_by: 'current_user@example.com' 
        })
      });
    } catch (err) {
      console.error(err);
      fetchApprovals();
      alert('Error submitting decision.');
    }
  };

  const filteredApprovals = approvals.filter(a => {
    if (activeTab === 'pending') return a.status === 'pending';
    if (activeTab === 'approved') return a.status === 'approve' || a.status === 'approved';
    if (activeTab === 'rejected') return a.status === 'reject' || a.status === 'rejected';
    if (activeTab === 'delegated') return a.status === 'delegate' || a.status === 'delegated';
    return false;
  }).sort((a, b) => {
    if (!a.due_by) return 1;
    if (!b.due_by) return -1;
    return new Date(a.due_by).getTime() - new Date(b.due_by).getTime();
  });

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header & Tabs */}
      <div className="sticky top-0 z-10 bg-[#0a0a0c]/90 backdrop-blur-md border-b border-white/10 px-4 sm:px-8 pt-6 pb-0">
        <div className="flex justify-between items-end mb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Approvals Queue</h1>
            <p className="text-muted-foreground text-sm mt-1">Review and action pending requests.</p>
          </div>
          <button className="p-2 bg-white/5 hover:bg-white/10 rounded-md border border-white/10 transition-colors">
            <Filter className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        <div className="flex overflow-x-auto no-scrollbar">
          {(['pending', 'approved', 'rejected', 'delegated'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={clsx(
                "px-6 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap capitalize",
                activeTab === tab 
                  ? "border-primary text-primary" 
                  : "border-transparent text-muted-foreground hover:text-white hover:bg-white/5"
              )}
            >
              {tab}
              {tab === 'pending' && (
                <span className={clsx(
                  "ml-2 text-[10px] px-2 py-0.5 rounded-full font-bold transition-colors",
                  activeTab === tab ? "bg-primary/20 text-primary" : "bg-white/10 text-white"
                )}>
                  {approvals.filter(a => a.status === 'pending').length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-8">
        <div className="max-w-4xl mx-auto space-y-4">
          <AnimatePresence mode="popLayout">
            {loading ? (
              <div className="text-center py-12 text-muted-foreground">Loading queue...</div>
            ) : filteredApprovals.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="text-center py-24"
              >
                <CheckCircle className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">You're all caught up!</h3>
                <p className="text-muted-foreground">No {activeTab} approvals at the moment.</p>
              </motion.div>
            ) : (
              filteredApprovals.map(approval => (
                <ApprovalCard 
                  key={approval.id} 
                  approval={approval} 
                  isActive={activeTab === 'pending'}
                  isExpanded={expandedId === approval.id}
                  onToggleExpand={() => setExpandedId(expandedId === approval.id ? null : approval.id)}
                  onDecision={handleDecision}
                />
              ))
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

// --- Subcomponent: ApprovalCard with Swipe Gestures ---

interface ApprovalCardProps {
  approval: Approval;
  isActive: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onDecision: (id: string, decision: string) => void;
}

const ApprovalCard: React.FC<ApprovalCardProps> = ({ approval, isActive, isExpanded, onToggleExpand, onDecision }) => {
  const controls = useAnimation();
  
  useEffect(() => {
    controls.start({ opacity: 1, y: 0, x: 0 });
  }, [controls]);

  const handleDragEnd = async (_event: any, info: any) => {
    const threshold = 100;
    if (info.offset.x > threshold) {
      await controls.start({ x: '100%', opacity: 0 });
      onDecision(approval.id, 'approved');
    } else if (info.offset.x < -threshold) {
      await controls.start({ x: '-100%', opacity: 0 });
      onDecision(approval.id, 'rejected');
    } else {
      controls.start({ x: 0 });
    }
  };

  const urgencyClass = () => {
    if (!approval.due_by) return 'text-muted-foreground';
    const hours = (new Date(approval.due_by).getTime() - Date.now()) / 3600000;
    if (hours < 24) return 'text-red-400 font-bold';
    if (hours < 72) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={controls}
      exit={{ opacity: 0, scale: 0.95 }}
      drag={isActive ? "x" : false}
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={handleDragEnd}
      className="relative bg-[#111115] border border-white/10 rounded-xl shadow-lg overflow-hidden group touch-pan-y"
    >
      {/* Swipe Indicators (visible on drag) */}
      <div className="absolute inset-y-0 left-0 w-1/2 bg-green-500/20 flex items-center px-6 -z-10 opacity-0 group-active:opacity-100 transition-opacity">
        <Check className="w-8 h-8 text-green-500" />
      </div>
      <div className="absolute inset-y-0 right-0 w-1/2 bg-red-500/20 flex items-center justify-end px-6 -z-10 opacity-0 group-active:opacity-100 transition-opacity">
        <X className="w-8 h-8 text-red-500" />
      </div>

      <div className="bg-[#111115] p-5 sm:p-6 h-full cursor-pointer" onClick={onToggleExpand}>
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white group-hover:text-primary transition-colors">
              {approval.title}
            </h3>
            <div className="flex flex-wrap gap-4 mt-3 text-xs">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <User className="w-3.5 h-3.5" />
                <span>{approval.requested_by || 'Milo'}</span>
              </div>
              {approval.due_by && (
                <div className={`flex items-center gap-1.5 ${urgencyClass()}`}>
                  <Clock className="w-3.5 h-3.5" />
                  <span>Due {new Date(approval.due_by).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Quick Actions Desktop */}
          {isActive && (
            <div className="hidden sm:flex items-center gap-2" onClick={e => e.stopPropagation()}>
              <button 
                onClick={() => onDecision(approval.id, 'approved')}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-green-500/10 text-green-500 hover:bg-green-500 hover:text-white border border-green-500/20 transition-all"
                title="Approve"
              >
                <Check className="w-5 h-5" />
              </button>
              <button 
                onClick={() => onDecision(approval.id, 'rejected')}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white border border-red-500/20 transition-all"
                title="Reject"
              >
                <X className="w-5 h-5" />
              </button>
              <button 
                onClick={() => onDecision(approval.id, 'delegate')}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-500/10 text-blue-500 hover:bg-blue-500 hover:text-white border border-blue-500/20 transition-all"
                title="Delegate"
              >
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>

        {/* Expandable Details */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-6 mt-4 border-t border-white/5">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {approval.description || 'No additional context provided.'}
                  </div>
                </div>
                
                {/* Mobile inline actions */}
                {isActive && (
                  <div className="sm:hidden grid grid-cols-2 gap-3 mt-6" onClick={e => e.stopPropagation()}>
                    <button 
                      onClick={() => onDecision(approval.id, 'approved')}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-green-500/20 text-green-400 border border-green-500/30 font-medium active:bg-green-500 active:text-white transition-colors"
                    >
                      <Check className="w-4 h-4" /> Approve
                    </button>
                    <button 
                      onClick={() => onDecision(approval.id, 'rejected')}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 font-medium active:bg-red-500 active:text-white transition-colors"
                    >
                      <X className="w-4 h-4" /> Reject
                    </button>
                    <button 
                      onClick={() => onDecision(approval.id, 'delegate')}
                      className="col-span-2 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-white/5 text-muted-foreground border border-white/10 font-medium active:bg-white/10 transition-colors"
                    >
                      <ArrowRight className="w-4 h-4" /> Delegate
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default Approvals;
