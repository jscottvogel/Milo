"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchActivities } from "@/lib/api";
import { Activity, Mail, CheckCircle2, ShieldAlert, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

export function MiloActivityFeed() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['activities'],
    queryFn: fetchActivities,
    refetchInterval: 15000,
  });

  if (isLoading) {
    return <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col text-muted-foreground animate-pulse min-h-[250px]">Loading activity...</div>;
  }

  if (error || !data) {
    return <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex items-center justify-center text-red-400 min-h-[250px]">Failed to load activity feed.</div>;
  }

  const activities = data || [];
  
  if (activities.length === 0) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col items-center justify-center text-muted-foreground min-h-[250px] text-center">
        <Activity className="w-6 h-6 mb-2 opacity-50 text-indigo-400" />
        <p className="text-sm font-medium text-white">Milo is resting</p>
        <p className="text-xs mt-1 opacity-70">No recent autonomous actions taken.</p>
      </div>
    );
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col min-h-[250px]">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-lg text-white flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-400" />
          Milo Activity
        </h3>
        <span className="flex items-center gap-1.5 text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20 font-medium">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
          </span>
          LIVE
        </span>
      </div>
      <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
        <div className="relative pl-3 border-l border-white/10 space-y-4">
          {activities.map((item: any, i: number) => {
            let Icon = Cpu;
            let iconColor = "text-indigo-400 bg-indigo-500/10 border-indigo-500/20";
            
            if (item.type === 'email') {
              Icon = Mail;
              iconColor = "text-blue-400 bg-blue-500/10 border-blue-500/20";
            } else if (item.type === 'approval') {
              Icon = CheckCircle2;
              iconColor = "text-green-400 bg-green-500/10 border-green-500/20";
            } else if (item.type === 'system') {
              Icon = ShieldAlert;
              iconColor = "text-amber-400 bg-amber-500/10 border-amber-500/20";
            }

            return (
              <div key={item.id || i} className="relative">
                <div className={cn("absolute -left-[23px] top-0 p-1 rounded-full border bg-black/50 z-10", iconColor)}>
                  <Icon className="w-3 h-3" />
                </div>
                <div className="pl-3">
                  <p className="text-sm text-white/90 leading-snug">{item.action}</p>
                  <span className="text-xs text-muted-foreground mt-0.5 block">{item.time}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
