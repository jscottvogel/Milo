import { useEffect, useState } from 'react';
import { Target, Activity, CheckCircle2, CircleDashed, Rocket, Loader2, Play, CalendarClock, AlertTriangle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';

interface DashboardData {
  root_items: any[];
  next_up: any[];
  recently_completed: any[];
  high_risks: any[];
}

export function Programs() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const navigate = useNavigate();

  const fetchDashboard = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/v1/work_items/dashboard`, {
        headers: {
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
        }
      });
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
      
      const valRes = await fetch(`${API_URL}/v1/work_items/validation-errors`, {
        headers: {
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
        }
      });
      if (valRes.ok) {
        const valJson = await valRes.json();
        setValidationErrors(valJson.errors || []);
      }
    } catch (e) {
      console.error('Failed to fetch dashboard:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'executing':
      case 'in_progress':
        return <Activity className="text-blue-400" size={16} />;
      case 'completed':
      case 'closed':
      case 'done':
        return <CheckCircle2 className="text-emerald-400" size={16} />;
      case 'initiating':
      case 'planning':
      case 'pending':
        return <Play className="text-amber-400" size={16} />;
      default:
        return <CircleDashed className="text-muted-foreground" size={16} />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-muted-foreground z-10 gap-4">
        <Loader2 size={32} className="animate-spin text-primary" />
        <span>Loading dashboard...</span>
      </div>
    );
  }

  const { root_items = [], next_up = [], recently_completed = [], high_risks = [] } = data || {};

  return (
    <div className="flex flex-col h-full w-full max-w-7xl mx-auto p-8 z-10 overflow-y-auto scrollbar-hide">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <Target className="text-primary" size={32} />
            Executive Dashboard
          </h2>
          <p className="text-muted-foreground mt-2">Workspace overview, strategic objectives, and critical items needing attention.</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer text-sm text-muted-foreground hover:text-white transition-colors mr-4">
            <input 
              type="checkbox" 
              checked={showArchived} 
              onChange={(e) => setShowArchived(e.target.checked)}
              className="rounded border-white/20 bg-black/50 text-primary focus:ring-primary focus:ring-offset-0"
            />
            Show Archived
          </label>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-xl transition-colors font-medium shadow-lg shadow-primary/20">
            <Rocket size={18} />
            New Objective
          </button>
        </div>
      </div>

      {validationErrors.length > 0 && (
        <div className="mb-6 bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start gap-3 animate-fade-in">
          <AlertTriangle className="text-rose-400 shrink-0 mt-0.5" size={20} />
          <div>
            <h4 className="text-rose-400 font-semibold mb-1">⚠️ {validationErrors.length} hierarchy violations detected</h4>
            <ul className="list-disc list-inside text-sm text-rose-300/80 space-y-1">
              {validationErrors.slice(0, 3).map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
              {validationErrors.length > 3 && (
                <li className="italic text-rose-400/60 mt-1">...and {validationErrors.length - 3} more. Check reconciliation log.</li>
              )}
            </ul>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* Left Column: Root Items */}
        <div className="xl:col-span-2 space-y-6">
          <h3 className="text-xl font-semibold text-white flex items-center gap-2 mb-2">
            <Activity className="text-blue-400" size={24} /> Strategic Objectives
          </h3>
          
          {root_items.length === 0 ? (
            <div className="flex flex-col items-center justify-center glass-card border-dashed p-12 text-center animate-fade-in">
              <Target className="w-16 h-16 text-muted-foreground/30 mb-4" />
              <h3 className="text-xl font-medium text-white">No active objectives</h3>
              <p className="text-muted-foreground mt-2 max-w-sm">Ask Milo to create a new strategic objective to get started!</p>
            </div>
          ) : (
            <div className="space-y-6">
              {root_items.filter(i => showArchived || i.status !== 'archived').map((item) => (
                <div 
                  key={item.id} 
                  onClick={() => navigate(`/programs/${item.id}`)}
                  className={clsx(
                    "glass-card p-6 animate-slide-up flex flex-col relative overflow-hidden group hover:border-white/20 transition-all hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] cursor-pointer",
                    item.status === 'archived' && "opacity-60 grayscale"
                  )}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                         <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-white/10 text-white border border-white/10">
                            {item.item_type}
                         </span>
                      </div>
                      <h3 className={clsx("text-2xl font-bold transition-colors", item.status === 'archived' ? 'text-gray-400 line-through' : 'text-white group-hover:text-primary')}>{item.name}</h3>
                      {item.description && (
                        <p className="text-sm text-gray-400 mt-2 line-clamp-2 max-w-2xl">{item.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/40 border border-white/5 whitespace-nowrap shadow-inner">
                      {getStatusIcon(item.status)}
                      <span className="text-xs font-semibold text-gray-200 capitalize">{item.status}</span>
                    </div>
                  </div>
                  <div className="pt-2 flex items-center text-sm text-primary group-hover:text-primary-hover font-medium transition-colors">
                      View Hierarchy <ArrowRight size={14} className="ml-1" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>


        {/* Right Column: Feeds */}
        <div className="space-y-8">
          
          {/* Critical Risks */}
          <section>
             <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
               <AlertTriangle className="text-rose-400" size={20} /> Critical Risks
             </h3>
             {high_risks.length === 0 ? (
               <div className="glass-card p-4 text-center text-sm text-muted-foreground border-dashed border-white/10">
                 No critical risks identified.
               </div>
             ) : (
               <div className="space-y-3">
                 {high_risks.filter(r => showArchived || r.status !== 'archived').map((risk: any) => (
                   <div key={risk.id} className={clsx("glass-card p-4 border-l-2 flex flex-col gap-2", risk.status === 'archived' ? "border-l-gray-500/50 opacity-60" : "border-l-rose-500/50")}>
                     <div className="flex items-start justify-between">
                       <span className="text-xs font-medium text-rose-300/80 uppercase tracking-wider">{risk.program_name}</span>
                       <span className="text-xs bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded">{risk.status}</span>
                     </div>
                     <p className={clsx("text-sm font-medium", risk.status === 'archived' ? 'text-gray-400 line-through' : 'text-white')}>{risk.title}</p>
                     <div className="flex gap-4 text-xs text-muted-foreground mt-1">
                        <span>Impact: <strong className="text-rose-400">{risk.impact}/5</strong></span>
                        <span>Likelihood: <strong className="text-rose-400">{risk.likelihood}/5</strong></span>
                     </div>
                   </div>
                 ))}
               </div>
             )}
          </section>

          {/* Next Up */}
          <section>
             <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
               <CalendarClock className="text-blue-400" size={20} /> Next Up
             </h3>
             {next_up.length === 0 ? (
               <div className="glass-card p-4 text-center text-sm text-muted-foreground border-dashed border-white/10">
                 No upcoming tasks.
               </div>
             ) : (
               <div className="space-y-3">
                 {next_up.filter(t => showArchived || t.status !== 'archived').map((task: any) => (
                   <div key={task.id} className={clsx("glass-card p-4 transition-colors group", task.status === 'archived' ? "opacity-60" : "hover:border-blue-500/30")}>
                     <div className="flex items-start justify-between mb-1">
                       <span className="text-xs font-medium text-blue-300/80 uppercase tracking-wider line-clamp-1">{task.program_name}</span>
                       {task.due_date && (
                         <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                           Due {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                         </span>
                       )}
                     </div>
                     <p className={clsx("text-sm font-medium transition-colors", task.status === 'archived' ? 'text-gray-400 line-through' : 'text-white group-hover:text-blue-100')}>{task.title}</p>
                     {task.owner_name && (
                       <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1.5">
                         <span className="w-4 h-4 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[8px] font-bold text-white shadow-lg shrink-0">
                           {task.owner_name.charAt(0).toUpperCase()}
                         </span>
                         {task.owner_name}
                       </p>
                     )}
                   </div>
                 ))}
               </div>
             )}
          </section>

          {/* Recently Completed */}
          <section>
             <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
               <CheckCircle2 className="text-emerald-400" size={20} /> Recently Completed
             </h3>
             {recently_completed.length === 0 ? (
               <div className="glass-card p-4 text-center text-sm text-muted-foreground border-dashed border-white/10">
                 No recent completions.
               </div>
             ) : (
               <div className="space-y-3">
                 {recently_completed.map((task: any) => (
                   <div key={task.id} className="glass-card p-4 border border-emerald-500/10 hover:border-emerald-500/30 transition-colors group">
                     <div className="flex items-start justify-between mb-1">
                       <span className="text-xs font-medium text-emerald-300/80 uppercase tracking-wider line-clamp-1">{task.program_name}</span>
                     </div>
                     <p className="text-sm font-medium text-gray-300 line-through group-hover:text-emerald-100 transition-colors">{task.title}</p>
                   </div>
                 ))}
               </div>
             )}
          </section>

        </div>
      </div>
    </div>
  );
}
