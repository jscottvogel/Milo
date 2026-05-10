"use client";

import { AlertTriangle, CheckCircle, Clock, FileText, Mail } from "lucide-react";
import { cn } from "@/lib/utils";

interface FeedItem {
  id: string;
  type: 'approval' | 'overdue' | 'email' | 'risk' | 'decision';
  title: string;
  subtitle: string;
  urgency: 'high' | 'medium' | 'low';
  timeAgo: string;
}

import { useQuery } from "@tanstack/react-query";
import { fetchDashboard } from "@/lib/api";

const ICONS: Record<string, any> = {
  approval: CheckCircle,
  overdue: Clock,
  email: Mail,
  risk: AlertTriangle,
  decision: FileText,
};

export function AttentionRequiredFeed() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden flex flex-col h-full p-4 text-muted-foreground animate-pulse">Loading alerts...</div>;
  }

  if (error || !data) {
    return <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden flex flex-col h-full p-4 text-red-400">Failed to load alerts.</div>;
  }

  // Combine high risks and next_up tasks into a single feed
  const feedItems: FeedItem[] = [];

  // Add high risks
  (data.high_risks || []).forEach((risk: any) => {
    feedItems.push({
      id: risk.id,
      type: 'risk',
      title: risk.title,
      subtitle: `Impact: ${risk.impact}/5, Likelihood: ${risk.likelihood}/5`,
      urgency: 'high',
      timeAgo: 'Now'
    });
  });

  // Add next_up tasks
  (data.next_up || []).forEach((task: any) => {
    const isOverdue = task.due_date && new Date(task.due_date).getTime() < new Date().getTime();
    feedItems.push({
      id: task.id,
      type: isOverdue ? 'overdue' : 'approval', // using approval icon just for 'todo' tasks visually for now
      title: task.name,
      subtitle: `${task.owner_name || 'Unassigned'} • ${task.status}`,
      urgency: isOverdue ? 'high' : 'medium',
      timeAgo: task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No date'
    });
  });

  // Add empty state if needed
  if (feedItems.length === 0) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden flex flex-col h-full items-center justify-center p-8 text-center">
        <CheckCircle className="w-8 h-8 mb-3 text-green-500 opacity-80" />
        <h3 className="font-semibold text-lg text-white">All Clear</h3>
        <p className="text-muted-foreground text-sm mt-1">No risks or overdue tasks require your attention right now.</p>
      </div>
    );
  }
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden flex flex-col h-full">
      <div className="p-4 border-b border-white/10 bg-black/20 flex justify-between items-center">
        <h3 className="font-semibold text-lg flex items-center gap-2">
          Attention Required
          <span className="bg-red-500/20 text-red-400 text-xs py-0.5 px-2 rounded-full border border-red-500/30">
            {feedItems.filter(i => i.urgency === 'high').length} Urgent
          </span>
        </h3>
      </div>
      <div className="flex-1 overflow-auto p-2 space-y-1">
        {feedItems.map(item => {
          const Icon = ICONS[item.type] || CheckCircle;
          return (
            <div 
              key={item.id} 
              className={cn(
                "p-3 rounded-lg flex items-start gap-3 hover:bg-white/10 transition-colors cursor-pointer group border border-transparent",
                item.urgency === 'high' && "hover:border-red-500/30"
              )}
            >
              <div className={cn(
                "p-2 rounded-lg shrink-0",
                item.urgency === 'high' ? "bg-red-500/10 text-red-400" : "bg-white/5 text-muted-foreground"
              )}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-start gap-2">
                  <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors truncate">
                    {item.title}
                  </h4>
                  <span className="text-xs text-muted-foreground shrink-0 mt-0.5">{item.timeAgo}</span>
                </div>
                <p className="text-xs text-muted-foreground truncate mt-0.5">
                  {item.subtitle}
                </p>
                {/* Inline Action */}
                <div className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button className="text-xs bg-white/10 hover:bg-white/20 text-white px-3 py-1 rounded transition-colors">
                    {item.type === 'risk' ? 'Assign Mitigation' : 'View Details'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
