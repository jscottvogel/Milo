import React, { useState, useEffect } from 'react';

// Types
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
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [notes, setNotes] = useState('');

  const fetchApprovals = async () => {
    try {
      // In a real app, you'd attach the tenant JWT auth token here
      const res = await fetch('/v1/approvals'); 
      if (res.ok) {
        const data = await res.json();
        // Sort by due_by ASC
        const pending = (data.approvals || []).filter((a: Approval) => a.status === 'pending');
        pending.sort((a: Approval, b: Approval) => {
          if (!a.due_by) return 1;
          if (!b.due_by) return -1;
          return new Date(a.due_by).getTime() - new Date(b.due_by).getTime();
        });
        setApprovals(pending);
      }
    } catch (err) {
      console.error('Failed to fetch approvals', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
    // Poll every 15 seconds for real-time updates
    const interval = setInterval(fetchApprovals, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (approvalId: string, decision: string) => {
    try {
      const res = await fetch(`/v1/approvals/${approvalId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          notes,
          decided_by: 'current_user@example.com' // Should be pulled from context
        })
      });
      
      if (res.ok) {
        setSelectedApproval(null);
        setNotes('');
        fetchApprovals();
      } else {
        alert('Failed to submit decision.');
      }
    } catch (err) {
      console.error(err);
      alert('Error submitting decision.');
    }
  };

  if (loading) return <div className="p-4">Loading Approvals Queue...</div>;

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold mb-6">Approvals Queue</h1>
      
      {approvals.length === 0 ? (
        <div className="text-gray-500">No pending approvals.</div>
      ) : (
        <div className="flex flex-col gap-4">
          {approvals.map(approval => (
            <div 
              key={approval.id} 
              className="bg-white border rounded-lg shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSelectedApproval(approval)}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-lg">{approval.title}</h3>
                <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full uppercase font-bold">
                  {approval.status}
                </span>
              </div>
              <div className="text-sm text-gray-600 mb-4 flex flex-col sm:flex-row sm:gap-4">
                <span><strong>Requested By:</strong> {approval.requested_by || 'Milo'}</span>
                {approval.due_by && (
                  <span className="text-red-600">
                    <strong>Due:</strong> {new Date(approval.due_by).toLocaleString()}
                  </span>
                )}
              </div>
              
              {/* Quick Actions (Mobile friendly) */}
              <div className="flex flex-wrap gap-2 mt-2" onClick={(e) => e.stopPropagation()}>
                <button 
                  onClick={() => handleDecision(approval.id, 'approve')}
                  className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                >
                  Approve
                </button>
                <button 
                  onClick={() => handleDecision(approval.id, 'reject')}
                  className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {selectedApproval && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">{selectedApproval.title}</h2>
            
            <div className="bg-gray-50 p-4 rounded mb-4 text-sm whitespace-pre-wrap">
              {selectedApproval.description || 'No description provided.'}
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">Notes / Instructions (Optional)</label>
              <textarea 
                className="w-full border rounded p-2 text-sm"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add context to your decision..."
              />
            </div>

            <div className="flex flex-wrap gap-2 justify-end">
              <button 
                onClick={() => setSelectedApproval(null)}
                className="px-4 py-2 border rounded hover:bg-gray-100"
              >
                Close
              </button>
              {(selectedApproval.options || ['approve', 'reject', 'delegate', 'defer']).map(opt => (
                <button 
                  key={opt}
                  onClick={() => handleDecision(selectedApproval.id, opt)}
                  className={`px-4 py-2 rounded text-white capitalize ${
                    opt === 'approve' ? 'bg-green-600 hover:bg-green-700' :
                    opt === 'reject' ? 'bg-red-600 hover:bg-red-700' :
                    opt === 'delegate' ? 'bg-blue-600 hover:bg-blue-700' :
                    'bg-gray-600 hover:bg-gray-700'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Approvals;
