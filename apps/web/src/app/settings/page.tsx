"use client";

import { useAppStore, UserRole } from "@/store/useAppStore";
import { Building, Users, Link as LinkIcon, Database, ShieldAlert, Download, Save, Check, Clock, Play } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

import { useEffect } from "react";
import { fetchTenant, fetchIntegrations, fetchJobs, triggerJob } from "@/lib/api";

const DEFAULT_INTEGRATIONS = [
  { id: "nylas-email", name: "Nylas Email", status: "disconnected" },
  { id: "nylas-cal", name: "Nylas Calendar", status: "disconnected" },
  { id: "stripe", name: "Stripe", status: "disconnected" },
  { id: "github", name: "GitHub", status: "disconnected" },
  { id: "docusign", name: "DocuSign", status: "disconnected" },
  { id: "hubspot", name: "HubSpot", status: "disconnected" },
];

const ROLES: UserRole[] = ['Executive', 'PM', 'Engineer', 'Finance', 'Stakeholder', 'Admin'];

export default function Settings() {
  const { userRole, setUserRole } = useAppStore();
  const [saved, setSaved] = useState(false);
  const [tenantName, setTenantName] = useState("Loading...");
  const [integrations, setIntegrations] = useState(DEFAULT_INTEGRATIONS);
  const [jobs, setJobs] = useState<any[]>([]);
  const [runningJob, setRunningJob] = useState<string | null>(null);

  useEffect(() => {
    fetchTenant().then(t => setTenantName(t.name || "Acme Corp")).catch(console.error);
    fetchIntegrations().then((data: any[]) => {
      const isGmailConnected = data.some(i => i.provider === 'gmail' && i.status === 'connected');
      setIntegrations([
        { id: "nylas-email", name: "Nylas Email", status: isGmailConnected ? "connected" : "disconnected" },
        { id: "nylas-cal", name: "Nylas Calendar", status: isGmailConnected ? "connected" : "disconnected" },
        { id: "stripe", name: "Stripe", status: "disconnected" },
        { id: "github", name: "GitHub", status: "disconnected" },
        { id: "docusign", name: "DocuSign", status: "disconnected" },
        { id: "hubspot", name: "HubSpot", status: "disconnected" },
      ]);
    }).catch(console.error);

    fetchJobs().then(data => setJobs(data.jobs || [])).catch(console.error);
  }, []);

  const handleTrigger = async (jobId: string) => {
    setRunningJob(jobId);
    try {
      await triggerJob(jobId);
    } catch (e) {
      console.error("Failed to trigger job:", e);
    } finally {
      setRunningJob(null);
    }
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-6 h-full flex flex-col gap-8 overflow-y-auto custom-scrollbar max-w-5xl mx-auto w-full">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Workspace Settings</h1>
          <p className="text-muted-foreground">Manage your tenant configuration, integrations, and users.</p>
        </div>
        <button suppressHydrationWarning
          onClick={handleSave}
          className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saved ? "Saved" : "Save Changes"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Nav (Visual only) */}
        <div className="md:col-span-1 space-y-1">
          {[
            { id: 'profile', icon: Building, label: 'Tenant Profile', active: true },
            { id: 'jobs', icon: Clock, label: 'Scheduled Tasks', active: false },
            { id: 'users', icon: Users, label: 'User Management', active: false },
            { id: 'integrations', icon: LinkIcon, label: 'Integrations', active: false },
            { id: 'data', icon: Database, label: 'Data & Privacy', active: false },
            { id: 'audit', icon: ShieldAlert, label: 'Audit Logs', active: false },
          ].map(item => (
            <button suppressHydrationWarning key={item.id} className={cn(
              "w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors text-left",
              item.active ? "bg-white/10 text-white" : "text-muted-foreground hover:bg-white/5 hover:text-white"
            )}>
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}

          {/* Developer Sandbox for Role Switching */}
          <div className="pt-8 mt-8 border-t border-white/10">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider mb-4 px-4">Dev Tools: Persona Test</h3>
            <div className="px-4 space-y-2">
              <label className="text-xs text-muted-foreground block">Simulate Login As:</label>
              <select suppressHydrationWarning
                value={userRole}
                onChange={(e) => setUserRole(e.target.value as UserRole)}
                className="w-full bg-[#111115] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary/50"
              >
                {ROLES.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Settings Content */}
        <div className="md:col-span-2 space-y-8">
          
          {/* Tenant Profile */}
          <section className="bg-[#111115] border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Tenant Profile</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-1.5">Workspace Name</label>
                <input suppressHydrationWarning type="text" value={tenantName} onChange={(e) => setTenantName(e.target.value)} className="w-full max-w-md bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50" />
              </div>
              <div className="grid grid-cols-2 gap-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium text-white mb-1.5">Timezone</label>
                  <select suppressHydrationWarning className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50">
                    <option>America/Los_Angeles</option>
                    <option>America/New_York</option>
                    <option>UTC</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-1.5">Daily Briefing</label>
                  <div className="flex gap-2">
                    <select suppressHydrationWarning className="flex-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50">
                      <option>08:00 AM</option>
                      <option>09:00 AM</option>
                    </select>
                    <button suppressHydrationWarning className="px-4 bg-primary/20 text-primary border border-primary/30 rounded-lg text-sm font-medium">On</button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Integrations */}
          <section className="bg-[#111115] border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Connected Integrations</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {integrations.map(int => (
                <div key={int.id} className="border border-white/10 rounded-lg p-4 flex items-center justify-between bg-black/20">
                  <div className="font-medium text-white text-sm">{int.name}</div>
                  {int.status === 'connected' ? (
                    <span className="flex items-center gap-1.5 text-xs font-medium text-green-400 bg-green-500/10 px-2.5 py-1 rounded-full border border-green-500/20">
                      <Check className="w-3 h-3" /> Connected
                    </span>
                  ) : (
                    <button suppressHydrationWarning className="text-xs font-medium bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded transition-colors">
                      Connect
                    </button>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Scheduled Tasks */}
          <section className="bg-[#111115] border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Scheduled Background Tasks</h2>
            <div className="space-y-4">
              {jobs.map(job => (
                <div key={job.id} className="border border-white/10 rounded-lg p-4 flex items-center justify-between bg-black/20">
                  <div>
                    <div className="font-medium text-white text-sm">{job.name}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Schedule: <code className="text-primary bg-primary/10 px-1 py-0.5 rounded">{job.trigger}</code>
                      {job.next_run_time && <span className="ml-2">Next Run: {new Date(job.next_run_time).toLocaleString()}</span>}
                    </div>
                  </div>
                  <button suppressHydrationWarning
                    onClick={() => handleTrigger(job.id)}
                    disabled={runningJob === job.id}
                    className="flex items-center gap-2 text-xs font-medium bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded transition-colors disabled:opacity-50"
                  >
                    {runningJob === job.id ? (
                      <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Play className="w-3 h-3" />
                    )}
                    {runningJob === job.id ? "Running..." : "Run Now"}
                  </button>
                </div>
              ))}
              {jobs.length === 0 && (
                <div className="text-sm text-muted-foreground italic">No active scheduled jobs.</div>
              )}
            </div>
          </section>

          {/* Data & Audit */}
          <section className="bg-[#111115] border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Data & Compliance</h2>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-white mb-1.5">Data Retention Policy</label>
                <select suppressHydrationWarning className="w-full max-w-md bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50">
                  <option>90 Days (Default)</option>
                  <option>1 Year</option>
                  <option>Indefinite (Requires Enterprise)</option>
                </select>
                <p className="text-xs text-muted-foreground mt-2">Agent artifacts and communication logs will be purged after this window.</p>
              </div>

              <div className="pt-6 border-t border-white/10">
                <label className="block text-sm font-medium text-white mb-2">Audit Log Export</label>
                <div className="flex gap-3 max-w-md">
                  <input suppressHydrationWarning type="date" className="flex-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50" />
                  <span className="text-muted-foreground self-center">to</span>
                  <input suppressHydrationWarning type="date" className="flex-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50" />
                  <button suppressHydrationWarning className="bg-white/10 hover:bg-white/20 text-white px-4 py-2.5 rounded-lg transition-colors flex items-center justify-center">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
