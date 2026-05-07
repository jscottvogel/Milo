import { useState } from 'react';
import { Settings as SettingsIcon, CreditCard, User, Bell } from 'lucide-react';
import clsx from 'clsx';

export function Settings() {
  const [isLoading, setIsLoading] = useState(false);

  const handleManageSubscription = async () => {
    setIsLoading(true);
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/v1/billing/portal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
        },
        body: JSON.stringify({ return_url: window.location.href })
      });
      
      if (res.ok) {
        const data = await res.json();
        // Redirect to Stripe mock portal
        window.location.href = data.url;
      }
    } catch (e) {
      console.error("Failed to generate billing portal URL", e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto p-8 z-10 overflow-y-auto scrollbar-hide">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <SettingsIcon className="text-primary" size={32} />
          Settings
        </h2>
        <p className="text-muted-foreground mt-2">Manage your workspace configuration and billing.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Sidebar Nav */}
        <div className="space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-primary/10 text-primary font-medium">
            <CreditCard size={18} />
            Billing & Plans
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:bg-white/5 hover:text-white transition-colors">
            <User size={18} />
            Profile
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:bg-white/5 hover:text-white transition-colors">
            <Bell size={18} />
            Notifications
          </button>
        </div>

        {/* Content Panel */}
        <div className="md:col-span-2 space-y-6">
          <div className="glass-card p-6 animate-fade-in">
            <h3 className="text-xl font-medium text-white mb-2">Current Plan</h3>
            <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 flex items-center justify-between mt-4">
              <div>
                <p className="text-primary font-semibold text-lg">Pro Tier</p>
                <p className="text-sm text-muted-foreground">Billed monthly at $49.00</p>
              </div>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-full border border-green-500/20">
                Active
              </span>
            </div>

            <div className="mt-8 pt-6 border-t border-white/10">
              <h4 className="font-medium text-white mb-2">Manage Subscription</h4>
              <p className="text-sm text-muted-foreground mb-6">
                Update your payment method, download past invoices, or change your billing cycle through our secure Stripe portal.
              </p>
              
              <button 
                onClick={handleManageSubscription}
                disabled={isLoading}
                className={clsx(
                  "py-2.5 px-6 rounded-xl bg-surface hover:bg-white/10 border border-white/10 text-white font-medium transition-all flex items-center justify-center min-w-[200px]",
                  isLoading && "opacity-50 cursor-not-allowed"
                )}
              >
                {isLoading ? "Loading Portal..." : "Open Billing Portal"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
