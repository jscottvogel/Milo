"use client";

import { AlertCircle, Calendar, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProgramStatus {
  id: string;
  name: string;
  ragStatus: 'green' | 'amber' | 'red';
  progress: number;
  daysToNextMilestone: number;
  owner: string;
  summary: string;
}

import { useQuery } from "@tanstack/react-query";
import { fetchDashboard } from "@/lib/api";

export function PortfolioHealthStrip() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 30000, // Refetch every 30s for live feel
  });

  if (isLoading) {
    return <div className="text-muted-foreground animate-pulse p-4">Loading portfolio health...</div>;
  }

  if (error || !data) {
    return <div className="text-red-400 p-4">Failed to load portfolio data.</div>;
  }

  const rootItems = data.root_items || [];
  
  // If there are no programs, show a placeholder
  if (rootItems.length === 0) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center flex flex-col items-center justify-center text-muted-foreground">
        <AlertCircle className="w-8 h-8 mb-3 opacity-50" />
        <p>No active programs found.</p>
        <p className="text-sm mt-1 opacity-70">Ask Milo to create a new program to get started.</p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {rootItems.map((program: any) => {
        // Derive dynamic status/progress
        // In reality, this should be calculated from children status or metadata
        const progress = program.metadata_json?.progress || 0;
        const ragStatus = program.status === 'blocked' ? 'red' : (program.status === 'at_risk' ? 'amber' : 'green');
        const daysToNextMilestone = program.due_date ? Math.ceil((new Date(program.due_date).getTime() - new Date().getTime()) / (1000 * 3600 * 24)) : 0;
        const ownerName = program.owner_name || "Unassigned";
        const ownerInitials = ownerName !== "Unassigned" ? ownerName.split(' ').map((n: string) => n[0]).join('') : '?';
        const summary = program.description || "No description provided.";

        return (
          <div key={program.id} className="bg-white/5 border border-white/10 rounded-xl p-5 hover:bg-white/10 transition-colors cursor-pointer group flex flex-col gap-3">
            
            {/* Header */}
            <div className="flex justify-between items-start">
              <h3 className="font-semibold text-lg text-white group-hover:text-primary transition-colors">{program.name}</h3>
              <div className={cn(
                "px-2.5 py-0.5 rounded-full text-xs font-medium border flex items-center gap-1.5",
                ragStatus === 'green' && "bg-green-500/10 text-green-400 border-green-500/20",
                ragStatus === 'amber' && "bg-amber-500/10 text-amber-400 border-amber-500/20",
                ragStatus === 'red' && "bg-red-500/10 text-red-400 border-red-500/20"
              )}>
                <span className={cn(
                  "w-2 h-2 rounded-full",
                  ragStatus === 'green' && "bg-green-500",
                  ragStatus === 'amber' && "bg-amber-500",
                  ragStatus === 'red' && "bg-red-500"
                )} />
                <span className="capitalize">{ragStatus}</span>
              </div>
            </div>

            {/* Progress */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                <div 
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    ragStatus === 'green' && "bg-green-500",
                    ragStatus === 'amber' && "bg-amber-500",
                    ragStatus === 'red' && "bg-red-500"
                  )}
                  style={{ width: `${progress}%` }} 
                />
              </div>
            </div>

            {/* Details */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
              <div className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4" />
                <span className={cn(daysToNextMilestone < 0 && "text-red-400 font-medium")}>
                  {daysToNextMilestone < 0 
                    ? `${Math.abs(daysToNextMilestone)} days late` 
                    : `${daysToNextMilestone} days to next`}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-[10px] text-primary border border-primary/30">
                  {ownerInitials}
                </div>
                <span className="truncate">{ownerName}</span>
              </div>
            </div>

            {/* Summary */}
            <div className="bg-black/20 p-3 rounded-lg border border-white/5 mt-auto text-sm italic text-muted-foreground leading-relaxed flex gap-2 items-start">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
              <p className="line-clamp-2">"{summary}"</p>
            </div>
            
          </div>
        );
      })}
    </div>
  );
}
