"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchPortfolio } from "@/lib/api";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { AlertCircle } from "lucide-react";

export function HealthRings() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['portfolio'],
    queryFn: () => fetchPortfolio(),
    refetchInterval: 300000, // 5 minutes
  });

  if (isLoading) {
    return <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex items-center justify-center text-muted-foreground animate-pulse min-h-[200px]">Loading health status...</div>;
  }

  if (error || !data) {
    return <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex items-center justify-center text-red-400 min-h-[200px]">Failed to load health status.</div>;
  }

  const rootItems = data.portfolio || [];
  
  if (rootItems.length === 0) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col items-center justify-center text-muted-foreground min-h-[200px] text-center">
        <AlertCircle className="w-6 h-6 mb-2 opacity-50" />
        <p className="text-sm font-medium text-white">No Programs Active</p>
        <p className="text-xs mt-1 opacity-70">Add programs to see health metrics</p>
      </div>
    );
  }

  let green = 0, amber = 0, red = 0;
  rootItems.forEach((p: any) => {
    if (p.health === 'red' || p.status === 'blocked') red++;
    else if (p.health === 'amber' || p.status === 'at_risk') amber++;
    else green++;
  });

  const chartData = [
    { name: 'On Track', value: green, color: '#22c55e' },
    { name: 'At Risk', value: amber, color: '#f59e0b' },
    { name: 'Off Track', value: red, color: '#ef4444' },
  ].filter(d => d.value > 0);

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 h-full flex flex-col">
      <h3 className="font-semibold text-lg text-white mb-2">Portfolio Health</h3>
      <div className="flex-1 flex items-center justify-between min-h-[150px]">
        <div className="w-1/2 h-full min-h-[150px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={60}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#111115', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                itemStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="w-1/2 flex flex-col gap-3 pl-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <div className="flex flex-col">
              <span className="text-xl font-bold text-white leading-none">{green}</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">On Track</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <div className="flex flex-col">
              <span className="text-xl font-bold text-white leading-none">{amber}</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">At Risk</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="flex flex-col">
              <span className="text-xl font-bold text-white leading-none">{red}</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Off Track</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
