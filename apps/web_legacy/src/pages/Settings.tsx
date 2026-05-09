import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Blocks, Settings as SettingsIcon, CreditCard, Mail, GitBranch, MessageSquare, Check } from 'lucide-react';
import clsx from 'clsx';

export const Settings: React.FC = () => {
  const { setBreadcrumbContext } = useAppStore();
  const [activeTab, setActiveTab] = useState<'integrations' | 'persona' | 'billing'>('integrations');

  useEffect(() => {
    setBreadcrumbContext([{ label: 'Settings', path: '/settings' }]);
  }, [setBreadcrumbContext]);

  return (
    <div className="flex flex-col h-full bg-background max-w-4xl mx-auto">
      {/* Header */}
      <div className="pt-8 px-6 sm:px-8 pb-6 border-b border-white/10">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Workspace Settings</h1>
        <p className="text-muted-foreground text-sm">Manage your Milo environment, integrations, and billing.</p>
      </div>

      <div className="flex flex-col md:flex-row h-full overflow-hidden">
        {/* Settings Nav */}
        <div className="w-full md:w-64 border-r border-white/10 p-4 sm:p-6 space-y-1">
          {[
            { id: 'integrations', label: 'Integrations', icon: Blocks },
            { id: 'persona', label: 'AI Persona', icon: SettingsIcon },
            { id: 'billing', label: 'Billing & Plans', icon: CreditCard },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                "w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors",
                activeTab === tab.id 
                  ? "bg-primary/10 text-primary" 
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 sm:p-8">
          <AnimatePresence mode="wait">
            {activeTab === 'integrations' && (
              <motion.div key="integrations" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2 className="text-xl font-semibold mb-6">Connected Apps</h2>
                <div className="space-y-4">
                  
                  {/* Nylas */}
                  <div className="flex items-center justify-between p-5 bg-[#111115] border border-white/10 rounded-xl">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded bg-white/5 flex items-center justify-center">
                        <Mail className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">Nylas (Email & Calendar)</h3>
                        <p className="text-sm text-muted-foreground">Connected as milo@example.com</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1.5 text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded">
                        <Check className="w-3 h-3" /> Active
                      </span>
                      <button className="text-sm text-red-400 hover:text-red-300">Disconnect</button>
                    </div>
                  </div>

                  {/* GitHub */}
                  <div className="flex items-center justify-between p-5 bg-[#111115] border border-white/10 rounded-xl">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded bg-white/5 flex items-center justify-center">
                        <GitBranch className="w-5 h-5 text-gray-300" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">GitHub</h3>
                        <p className="text-sm text-muted-foreground">Connected to acme-corp/milo</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1.5 text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded">
                        <Check className="w-3 h-3" /> Active
                      </span>
                      <button className="text-sm text-red-400 hover:text-red-300">Disconnect</button>
                    </div>
                  </div>

                  {/* Slack */}
                  <div className="flex items-center justify-between p-5 bg-[#111115] border border-white/10 rounded-xl">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded bg-white/5 flex items-center justify-center">
                        <MessageSquare className="w-5 h-5 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">Slack</h3>
                        <p className="text-sm text-muted-foreground">Not connected</p>
                      </div>
                    </div>
                    <button className="text-sm px-4 py-1.5 bg-white/10 hover:bg-white/20 rounded transition-colors">
                      Connect
                    </button>
                  </div>

                </div>
              </motion.div>
            )}

            {activeTab === 'persona' && (
              <motion.div key="persona" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2 className="text-xl font-semibold mb-6">AI Persona Tuning</h2>
                <div className="space-y-8 max-w-lg">
                  
                  <div>
                    <div className="flex justify-between mb-2">
                      <label className="text-sm font-medium">Communication Tone</label>
                      <span className="text-xs text-primary">Professional</span>
                    </div>
                    <input type="range" className="w-full accent-primary" min="0" max="100" defaultValue="50" />
                    <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                      <span>Casual</span>
                      <span>Formal</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <label className="text-sm font-medium">Verbosity</label>
                      <span className="text-xs text-primary">Concise</span>
                    </div>
                    <input type="range" className="w-full accent-primary" min="0" max="100" defaultValue="25" />
                    <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                      <span>Bullet Points</span>
                      <span>Detailed Paragraphs</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-white/10">
                    <h3 className="text-sm font-semibold mb-4">Escalation Thresholds</h3>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3">
                        <input type="checkbox" defaultChecked className="rounded border-white/20 bg-transparent text-primary focus:ring-primary focus:ring-offset-background" />
                        <span className="text-sm">Require approval for budget increases over $1,000</span>
                      </label>
                      <label className="flex items-center gap-3">
                        <input type="checkbox" defaultChecked className="rounded border-white/20 bg-transparent text-primary focus:ring-primary focus:ring-offset-background" />
                        <span className="text-sm">Require approval for scope changes</span>
                      </label>
                      <label className="flex items-center gap-3">
                        <input type="checkbox" className="rounded border-white/20 bg-transparent text-primary focus:ring-primary focus:ring-offset-background" />
                        <span className="text-sm">Require approval for all outbound emails</span>
                      </label>
                    </div>
                  </div>

                  <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors">
                    Save Persona Settings
                  </button>
                </div>
              </motion.div>
            )}

            {activeTab === 'billing' && (
              <motion.div key="billing" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2 className="text-xl font-semibold mb-6">Billing & Plans</h2>
                
                <div className="bg-gradient-to-br from-primary/20 to-purple-500/10 border border-primary/30 rounded-xl p-6 mb-8 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-6">
                    <span className="bg-primary text-primary-foreground text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">Current Plan</span>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">Pro Tier</h3>
                  <p className="text-sm text-gray-300 mb-6 max-w-sm">Full autonomous capabilities with unlimited programs and integrations.</p>
                  
                  <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold">$499</span>
                    <span className="text-muted-foreground mb-1">/ month</span>
                  </div>
                </div>

                <h3 className="font-semibold mb-4">Recent Invoices</h3>
                <div className="border border-white/10 rounded-xl overflow-hidden">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-white/5 text-muted-foreground border-b border-white/10">
                      <tr>
                        <th className="px-4 py-3 font-medium">Date</th>
                        <th className="px-4 py-3 font-medium">Amount</th>
                        <th className="px-4 py-3 font-medium">Status</th>
                        <th className="px-4 py-3 font-medium text-right">Invoice</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {[
                        { date: 'May 1, 2026', amount: '$499.00', status: 'Paid' },
                        { date: 'Apr 1, 2026', amount: '$499.00', status: 'Paid' },
                        { date: 'Mar 1, 2026', amount: '$499.00', status: 'Paid' },
                      ].map((inv, i) => (
                        <tr key={i} className="hover:bg-white/[0.02]">
                          <td className="px-4 py-3 text-gray-300">{inv.date}</td>
                          <td className="px-4 py-3 text-white font-medium">{inv.amount}</td>
                          <td className="px-4 py-3">
                            <span className="text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded border border-green-500/20">{inv.status}</span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button className="text-primary hover:underline">Download</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default Settings;
