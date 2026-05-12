import { PortfolioHealthStrip } from "@/components/home/PortfolioHealthStrip";
import { AttentionRequiredFeed } from "@/components/home/AttentionRequiredFeed";
import { HealthRings } from "@/components/home/HealthRings";
import { UpcomingMilestones } from "@/components/home/UpcomingMilestones";
import { MiloActivityFeed } from "@/components/home/MiloActivityFeed";
import { QuickActionsBar } from "@/components/home/QuickActionsBar";

export default function HomeDashboard() {
  return (
    <div className="p-6 h-full flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Mission Control</h1>
          <p className="text-muted-foreground">Here's your executive briefing for today.</p>
        </div>
        <QuickActionsBar />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <HealthRings />
        </div>
        <div className="lg:col-span-2">
          <UpcomingMilestones />
        </div>
        <div className="lg:col-span-1">
          <MiloActivityFeed />
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 xl:grid-cols-3 gap-6 min-h-[400px]">
        {/* Column 1: Portfolio Health Strip (takes 2/3 space on large screens) */}
        <div className="xl:col-span-2 flex flex-col h-full">
          <div className="flex justify-between items-center mb-4 shrink-0">
            <h2 className="text-lg font-semibold text-white">Active Programs</h2>
            <button suppressHydrationWarning className="text-sm text-primary hover:text-primary/80 transition-colors">View All</button>
          </div>
          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <PortfolioHealthStrip />
          </div>
        </div>

        {/* Column 2: Attention Required (takes 1/3 space on large screens) */}
        <div className="flex flex-col h-full">
          <AttentionRequiredFeed />
        </div>
      </div>
    </div>
  );
}
