"use client";

import { Download, TrendingUp } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart
} from "recharts";
import { cn } from "@/lib/utils";

const DUMMY_FINANCIALS = [
  { period: "2026-01", budget: 10000, actual: 9500 },
  { period: "2026-02", budget: 15000, actual: 16200 },
  { period: "2026-03", budget: 12000, actual: 11000 },
  { period: "2026-04", budget: 18000, actual: 19500 },
  { period: "2026-05", budget: 20000, actual: 22000 },
];

export default function Financials() {
  const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

  const totalBudget = DUMMY_FINANCIALS.reduce((acc, curr) => acc + curr.budget, 0);
  const totalActual = DUMMY_FINANCIALS.reduce((acc, curr) => acc + curr.actual, 0);
  const totalVariance = totalActual - totalBudget;
  const variancePercent = (totalVariance / totalBudget) * 100;

  // Linear extrapolation for forecast
  const averageBurnRate = totalActual / DUMMY_FINANCIALS.length;
  const remainingPeriods = 3;
  const forecastToCompletion = totalActual + (averageBurnRate * remainingPeriods);

  return (
    <div className="flex flex-col gap-6 h-full overflow-y-auto pr-2 custom-scrollbar">
      
      {/* Header & KPIs */}
      <div className="flex justify-between items-start">
        <h2 className="text-xl font-bold text-white">Financial Performance</h2>
        <button className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-sm font-medium text-muted-foreground">Total Budget</span>
          <div className="text-2xl font-bold">{formatCurrency(totalBudget)}</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-sm font-medium text-muted-foreground">Total Actual</span>
          <div className="text-2xl font-bold">{formatCurrency(totalActual)}</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-sm font-medium text-muted-foreground">Variance</span>
          <div className={cn("text-2xl font-bold flex items-end gap-2", totalVariance > 0 ? "text-red-400" : "text-green-400")}>
            {formatCurrency(totalVariance)}
            <span className="text-sm font-normal mb-1">({variancePercent > 0 ? '+' : ''}{variancePercent.toFixed(1)}%)</span>
          </div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Forecast to Completion
          </span>
          <div className="text-2xl font-bold text-blue-400">{formatCurrency(forecastToCompletion)}</div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-[#111115] border border-white/10 rounded-xl p-6 h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={DUMMY_FINANCIALS}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
            <XAxis dataKey="period" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `$${value/1000}k`} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#111115', borderColor: '#ffffff20', borderRadius: '8px' }}
              itemStyle={{ color: '#fff' }}
              formatter={(value: number) => formatCurrency(value)}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Bar dataKey="budget" name="Budget" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={50} />
            <Bar dataKey="actual" name="Actual" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={50} />
            <Line type="monotone" dataKey="actual" name="Burn Trend" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Variance Table */}
      <div className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden mt-4">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#0a0a0c] border-b border-white/10 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-6 py-3 font-medium">Period</th>
              <th className="px-6 py-3 font-medium text-right">Budget</th>
              <th className="px-6 py-3 font-medium text-right">Actual</th>
              <th className="px-6 py-3 font-medium text-right">Variance ($)</th>
              <th className="px-6 py-3 font-medium text-right">Variance (%)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {DUMMY_FINANCIALS.map(row => {
              const variance = row.actual - row.budget;
              const variancePct = (variance / row.budget) * 100;
              const isOver = variance > 0;
              
              return (
                <tr key={row.period} className="hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 font-medium text-white">{row.period}</td>
                  <td className="px-6 py-4 text-right text-muted-foreground">{formatCurrency(row.budget)}</td>
                  <td className="px-6 py-4 text-right font-medium text-white">{formatCurrency(row.actual)}</td>
                  <td className={cn("px-6 py-4 text-right font-medium", isOver ? "text-red-400" : "text-green-400")}>
                    {isOver ? '+' : ''}{formatCurrency(variance)}
                  </td>
                  <td className={cn("px-6 py-4 text-right", isOver ? "text-red-400" : "text-green-400")}>
                    {isOver ? '+' : ''}{variancePct.toFixed(1)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
}
