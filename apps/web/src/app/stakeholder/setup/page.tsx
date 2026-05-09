"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function StakeholderSetupPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    fullName: "",
    title: "",
    preferredChannel: "email",
    frequency: "daily-digest"
  });
  
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // In a real app, we'd hit PUT /stakeholders/profile
    // For now, we simulate the delay and redirect
    setTimeout(() => {
      setLoading(false);
      router.push("/stakeholder");
    }, 1000);
  };

  return (
    <div className="max-w-xl mx-auto mt-12 bg-[#121218] p-8 rounded-xl border border-white/10 shadow-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Complete Your Profile</h1>
      <p className="text-white/60 mb-8">
        Welcome to Milo. Please confirm your details and communication preferences. 
        You retain control over this profile across all Milo programs.
      </p>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-white/80 mb-1">Full Name</label>
          <input 
            type="text" 
            required
            className="w-full bg-[#0a0a0c] border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
            value={form.fullName}
            onChange={e => setForm({...form, fullName: e.target.value})}
            placeholder="Jane Doe"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-white/80 mb-1">Title / Organization</label>
          <input 
            type="text" 
            className="w-full bg-[#0a0a0c] border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
            value={form.title}
            onChange={e => setForm({...form, title: e.target.value})}
            placeholder="VP of Engineering, Acme Corp"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-white/80 mb-1">Preferred Contact Channel</label>
          <select 
            className="w-full bg-[#0a0a0c] border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
            value={form.preferredChannel}
            onChange={e => setForm({...form, preferredChannel: e.target.value})}
          >
            <option value="email">Email</option>
            <option value="slack">Slack</option>
            <option value="teams">Microsoft Teams</option>
            <option value="sms">SMS</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-white/80 mb-1">Update Frequency</label>
          <select 
            className="w-full bg-[#0a0a0c] border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
            value={form.frequency}
            onChange={e => setForm({...form, frequency: e.target.value})}
          >
            <option value="real-time">Real-time (As it happens)</option>
            <option value="daily-digest">Daily Digest</option>
            <option value="weekly-summary">Weekly Summary</option>
          </select>
        </div>
        
        <button 
          type="submit" 
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-lg transition-colors mt-4"
        >
          {loading ? "Saving..." : "Save & Continue"}
        </button>
      </form>
    </div>
  );
}
