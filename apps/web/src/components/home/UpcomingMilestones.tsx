"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchDashboard } from "@/lib/api";
import { Calendar, CheckCircle2 } from "lucide-react";

export function UpcomingMilestones() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col text-muted-foreground animate-pulse min-h-[200px]">Loading milestones...</div>;
  }

  if (error || !data) {
    return <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex items-center justify-center text-red-400 min-h-[200px]">Failed to load milestones.</div>;
  }

  const nextUp = data.next_up || [];
  
  if (nextUp.length === 0) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col items-center justify-center text-muted-foreground min-h-[200px] text-center">
        <CheckCircle2 className="w-6 h-6 mb-2 opacity-50 text-green-500" />
        <p className="text-sm font-medium text-white">No upcoming milestones</p>
        <p className="text-xs mt-1 opacity-70">You are all caught up for the next 7 days</p>
      </div>
    );
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col min-h-[200px]">
      <h3 className="font-semibold text-lg text-white mb-3 flex items-center gap-2">
        <Calendar className="w-5 h-5 text-blue-400" />
        Upcoming (7 Days)
      </h3>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
        {nextUp.map((item: any) => {
          const isOverdue = item.due_date && new Date(item.due_date).getTime() < new Date().getTime();
          return (
            <div key={item.id} className="flex flex-col bg-black/20 rounded-lg p-3 border border-white/5 hover:border-white/10 transition-colors">
              <div className="flex justify-between items-start gap-2 mb-1">
                <span className="text-sm font-medium text-white truncate">{item.name}</span>
                <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${isOverdue ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-blue-500/10 text-blue-400 border-blue-500/20'}`}>
                  {isOverdue ? 'Overdue' : 'Due'}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs text-muted-foreground">
                <span className="truncate">{item.owner_name || 'Unassigned'}</span>
                <span>{item.due_date ? new Date(item.due_date).toLocaleDateString() : 'No Date'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
