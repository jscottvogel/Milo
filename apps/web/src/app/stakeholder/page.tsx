"use client";

import { useQuery } from "@tanstack/react-query";

export default function StakeholderDashboard() {
  
  // In a real implementation we would fetch from /stakeholders/programs
  // For the UI demonstration, we will use mock data that reflects the cross-tenant design
  
  const mockPrograms = [
    {
      id: "1",
      name: "Project Alpha (Tenant A)",
      role: "Sponsor",
      status: "active",
      health: "amber",
      recentUpdate: "Risk identified in phase 2 delivery. Mitigation plan approved."
    },
    {
      id: "2",
      name: "Migration Initiative (Tenant B)",
      role: "Reviewer",
      status: "active",
      health: "green",
      recentUpdate: "All milestones on track. Awaiting approval on final architectural review."
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">My Programs</h1>
          <p className="text-white/60 mt-1">Cross-tenant overview of your active involvements.</p>
        </div>
        <button className="px-4 py-2 bg-[#121218] border border-white/10 rounded-lg text-sm hover:bg-white/5 transition-colors">
          Edit Profile
        </button>
      </div>
      
      <div className="grid grid-cols-1 gap-4">
        {mockPrograms.map(p => (
          <div key={p.id} className="bg-[#121218] border border-white/10 rounded-xl p-6 flex flex-col hover:border-white/20 transition-colors cursor-pointer">
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${p.health === 'green' ? 'bg-emerald-500' : p.health === 'amber' ? 'bg-amber-500' : 'bg-red-500'}`} />
                  <h3 className="text-xl font-semibold text-white">{p.name}</h3>
                </div>
                <div className="text-sm text-white/50 mt-1 ml-6">
                  Role: <span className="text-white/80">{p.role}</span>
                </div>
              </div>
              <div className="text-xs font-medium px-2 py-1 bg-white/5 rounded text-white/70">
                {p.status.toUpperCase()}
              </div>
            </div>
            
            <div className="ml-6 mt-2 p-4 bg-[#0a0a0c] rounded-lg border border-white/5">
              <div className="text-xs text-white/40 mb-1 uppercase tracking-wider font-semibold">Latest Update</div>
              <div className="text-sm text-white/80">{p.recentUpdate}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
