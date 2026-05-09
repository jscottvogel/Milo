import React, { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { CheckCircle, Clock, Zap, Plus, FileText, Flag, MessageSquare, Loader2 } from 'lucide-react';
import { apiFetch } from '../api/client';

export const Home: React.FC = () => {
  const { setBreadcrumbContext } = useAppStore();

  useEffect(() => {
    setBreadcrumbContext([{ label: 'Dashboard', path: '/home' }]);
  }, [setBreadcrumbContext]);

  const [dashboardData, setDashboardData] = React.useState<any>(null);
  const [approvalsData, setApprovalsData] = React.useState<any[]>([]);
  const [recentActivity, setRecentActivity] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [dashRes, appRes, actRes] = await Promise.all([
          apiFetch<any>('/v1/work_items/dashboard'),
          apiFetch<any>('/v1/approvals').catch(() => ({ approvals: [] })),
          apiFetch<any[]>('/v1/activities').catch(() => [])
        ]);
        setDashboardData(dashRes);
        setApprovalsData(appRes.approvals || []);
        setRecentActivity(actRes);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Calculate Health Data dynamically
  const healthData = React.useMemo(() => {
    if (!dashboardData) return [];
    let onTrack = 0;
    let atRisk = 0;
    let offTrack = 0;

    dashboardData.root_items.forEach((item: any) => {
      if (item.status === 'at_risk') atRisk++;
      else if (item.status === 'off_track') offTrack++;
      else onTrack++;
    });

    return [
      { name: 'On Track', value: onTrack || 1, color: '#22c55e' }, // fallback 1 to show empty green ring if none
      { name: 'At Risk', value: atRisk, color: '#eab308' },
      { name: 'Off Track', value: offTrack, color: '#ef4444' },
    ];
  }, [dashboardData]);



  const quickActions = [
    { icon: Plus, label: 'New Task', color: 'bg-blue-500/10 text-blue-500 border-blue-500/20' },
    { icon: FileText, label: 'Log Decision', color: 'bg-purple-500/10 text-purple-500 border-purple-500/20' },
    { icon: Flag, label: 'Flag Risk', color: 'bg-orange-500/10 text-orange-500 border-orange-500/20' },
    { icon: MessageSquare, label: 'Ask Milo', color: 'bg-green-500/10 text-green-500 border-green-500/20' },
  ];

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Header & Quick Actions */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : (
      <>
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <p className="text-muted-foreground mt-1">Here's what needs your attention today.</p>
        </div>
        
        <div className="flex gap-3 overflow-x-auto pb-2 md:pb-0 w-full md:w-auto">
          {quickActions.map((action, i) => (
            <button key={i} className={`flex items-center gap-2 px-4 py-2 rounded-full border hover:bg-white/5 transition-colors whitespace-nowrap ${action.color}`}>
              <action.icon className="w-4 h-4" />
              <span className="font-medium text-sm text-white">{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Program Health */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#111115]/80 backdrop-blur border border-white/10 rounded-xl p-6 flex flex-col"
        >
          <h3 className="font-semibold flex items-center gap-2 text-lg mb-4">
            <Zap className="w-5 h-5 text-yellow-500" />
            Program Health
          </h3>
          <div className="flex-1 flex items-center justify-center h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={healthData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {healthData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0a0a0c', borderColor: '#333', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4 text-center text-sm">
            {healthData.map(d => (
              <div key={d.name} className="flex flex-col items-center">
                <span className="font-bold text-lg" style={{ color: d.color }}>{d.value}</span>
                <span className="text-xs text-muted-foreground leading-tight">{d.name}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Top Approvals */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-[#111115]/80 backdrop-blur border border-white/10 rounded-xl p-6 flex flex-col md:col-span-2"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold flex items-center gap-2 text-lg">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Open Approvals
            </h3>
            <button className="text-xs text-primary hover:underline">View All</button>
          </div>
          
          <div className="space-y-3 flex-1">
            {approvalsData.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">No pending approvals.</div>
            ) : approvalsData.slice(0, 3).map((approval: any) => (
              <div key={approval.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors gap-4">
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm truncate">{approval.title}</h4>
                  <p className="text-xs text-muted-foreground mt-1">Requested by {approval.requested_by || 'Unknown'} • {approval.due_by ? 'Due ' + new Date(approval.due_by).toLocaleDateString() : 'No due date'}</p>
                </div>
                <div className="flex gap-2 w-full sm:w-auto">
                  <button className="flex-1 sm:flex-none px-3 py-1.5 text-xs font-medium bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded border border-green-500/20 transition-colors">
                    Approve
                  </button>
                  <button className="flex-1 sm:flex-none px-3 py-1.5 text-xs font-medium bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded border border-red-500/20 transition-colors">
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Upcoming Milestones */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-[#111115]/80 backdrop-blur border border-white/10 rounded-xl p-6 md:col-span-2"
        >
          <h3 className="font-semibold flex items-center gap-2 text-lg mb-4">
            <Clock className="w-5 h-5 text-blue-500" />
            Upcoming Milestones (14 Days)
          </h3>
          <div className="space-y-4">
            {dashboardData?.next_up?.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">No upcoming milestones.</div>
            ) : dashboardData?.next_up?.map((m: any) => (
              <div key={m.id} className="flex items-center gap-4 group cursor-pointer">
                <div className="w-10 h-10 rounded bg-white/5 flex flex-col items-center justify-center border border-white/10 flex-shrink-0 group-hover:border-primary/50 transition-colors">
                  <span className="text-[10px] text-muted-foreground uppercase">{m.due_date ? new Date(m.due_date).toLocaleDateString(undefined, { month: 'short' }) : 'TBD'}</span>
                  <span className="text-xs font-bold">{m.due_date ? new Date(m.due_date).getDate() : '-'}</span>
                </div>
                <div className="flex-1 min-w-0 border-b border-white/5 pb-4 group-last:border-0 group-last:pb-0">
                  <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors">{m.name}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-4 h-4 rounded-full bg-indigo-500 flex items-center justify-center text-[8px] font-bold">
                      {m.owner_name ? m.owner_name.substring(0, 2).toUpperCase() : 'NA'}
                    </div>
                    <span className="text-xs text-muted-foreground">{m.owner_name || 'Unassigned'} is the owner</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Milo Activity Feed */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-[#111115]/80 backdrop-blur border border-white/10 rounded-xl p-6"
        >
          <h3 className="font-semibold flex items-center gap-2 text-lg mb-4">
            <Zap className="w-5 h-5 text-primary" />
            Milo Activity
          </h3>
          <div className="relative border-l border-white/10 ml-3 space-y-6">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="relative pl-6">
                <div className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-primary ring-4 ring-[#111115]" />
                <p className="text-sm text-gray-300">{activity.action}</p>
                <span className="text-xs text-muted-foreground mt-1 block">{activity.time}</span>
              </div>
            ))}
          </div>
        </motion.div>

      </div>
      </>
      )}
    </div>
  );
};

export default Home;
