"use client";

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { 
  Home, 
  MessageSquare, 
  Package, 
  CheckCircle, 
  Inbox, 
  Settings as SettingsIcon,
  Search,
  Bell
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store/useAppStore';
import { RightRailChat } from './RightRailChat';
import { GlobalSearch } from './GlobalSearch';
import { RoleRedirect } from './RoleRedirect';

const navItems = [
  { path: '/home', icon: Home, label: 'Home' },
  { path: '/chat', icon: MessageSquare, label: 'Chat' },
  { path: '/programs', icon: Package, label: 'Programs' },
  { path: '/approvals', icon: CheckCircle, label: 'Approvals', badge: true },
  { path: '/inbox', icon: Inbox, label: 'Inbox' },
  { path: '/settings', icon: SettingsIcon, label: 'Settings' },
];

import { useEffect } from 'react';
import { usePendingApprovals } from '@/hooks/usePendingApprovals';

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const { isRightRailOpen, pendingApprovalsCount, setPendingApprovalsCount, breadcrumbContext, setSearchOpen, toggleRightRail } = useAppStore();
  const pathname = usePathname();

  const { count: pendingCount } = usePendingApprovals();
  
  useEffect(() => {
    setPendingApprovalsCount(pendingCount);
  }, [pendingCount, setPendingApprovalsCount]);

  // Basic breadcrumb fallback based on route if store is empty
  const defaultBreadcrumb = pathname.split('/').filter(Boolean).map(segment => ({
    label: segment.charAt(0).toUpperCase() + segment.slice(1),
    path: `/${segment}`
  }));

  const breadcrumbs = breadcrumbContext.length > 0 ? breadcrumbContext : defaultBreadcrumb;

  return (
    <div className="flex h-screen bg-background text-white overflow-hidden font-sans">
      <RoleRedirect />
      <GlobalSearch />
      
      {/* Sidebar */}
      <aside className="w-16 sm:w-64 flex-shrink-0 flex flex-col z-20 border-r border-border bg-[#0f0f13]">
        <div className="p-4 sm:p-6 h-16 flex items-center border-b border-border/50">
          <h1 className="text-xl sm:text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-400 hidden sm:block">
            Milo
          </h1>
          <div className="sm:hidden w-8 h-8 rounded bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center font-bold">
            M
          </div>
        </div>
        
        <nav className="flex-1 px-2 sm:px-4 py-6 space-y-1 sm:space-y-2">
          {navItems.map((item) => {
            const isActive = item.path !== '/chat' && pathname.startsWith(item.path);
            
            if (item.path === '/chat') {
              return (
                <button suppressHydrationWarning
                  key={item.path}
                  onClick={toggleRightRail}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 group relative text-muted-foreground hover:bg-white/5 hover:text-white"
                >
                  <div className="relative">
                    <item.icon className="w-5 h-5 group-hover:text-white" />
                  </div>
                  <span className="hidden sm:block">{item.label}</span>
                </button>
              );
            }

            return (
              <Link
                key={item.path}
                href={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 group relative',
                  isActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:bg-white/5 hover:text-white'
                )}
              >
                {isActive && (
                  <div className="absolute left-0 w-1 h-5 bg-primary rounded-r-full shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
                )}
                <div className="relative">
                  <item.icon className={cn("w-5 h-5", isActive ? "text-primary" : "group-hover:text-white")} />
                  {item.badge && pendingApprovalsCount > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold flex items-center justify-center rounded-full border-2 border-[#0f0f13]">
                      {pendingApprovalsCount}
                    </span>
                  )}
                </div>
                <span className="hidden sm:block">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className={cn(
        "flex-1 flex flex-col relative overflow-hidden bg-gradient-to-br from-[#0a0a0c] to-[#111115] transition-all duration-300",
        isRightRailOpen ? "sm:pr-[400px]" : ""
      )}>
        
        {/* Top Bar */}
        <header className="h-16 flex-shrink-0 flex items-center justify-between px-6 border-b border-border bg-[#0a0a0c]/80 backdrop-blur-md z-10">
          
          {/* Breadcrumbs */}
          <div className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <div key={crumb.path} className="flex items-center gap-2">
                {index > 0 && <span className="text-muted-foreground/50">/</span>}
                <span className={cn(
                  "truncate max-w-[150px] sm:max-w-[300px]",
                  index === breadcrumbs.length - 1 ? "text-white font-medium" : "text-muted-foreground hover:text-white cursor-pointer transition-colors"
                )}>
                  {crumb.label}
                </span>
              </div>
            ))}
            {breadcrumbs.length === 0 && <span className="text-white font-medium">Dashboard</span>}
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            <button suppressHydrationWarning
              onClick={() => setSearchOpen(true)}
              className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-md transition-colors border border-white/5"
            >
              <Search className="w-4 h-4" />
              <span>Search...</span>
              <kbd className="ml-4 text-[10px] bg-black/30 px-1.5 py-0.5 rounded border border-white/10">⌘K</kbd>
            </button>
            <button suppressHydrationWarning className="sm:hidden p-2 text-muted-foreground hover:text-white" onClick={() => setSearchOpen(true)}>
              <Search className="w-5 h-5" />
            </button>
            
            <button suppressHydrationWarning className="relative p-2 text-muted-foreground hover:text-white transition-colors rounded-full hover:bg-white/5">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-2 w-2 h-2 bg-primary rounded-full" />
            </button>
            
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-sm shadow-lg border border-white/10 cursor-pointer hover:ring-2 hover:ring-primary/50 transition-all">
              JS
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 relative overflow-auto pb-24 sm:pb-0">
          {/* Background noise and glows */}
          <div className="fixed inset-0 bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')] opacity-[0.03] pointer-events-none mix-blend-overlay"></div>
          
          <div className="relative z-10 w-full h-full">
            {children}
          </div>
        </main>
      </div>

      {/* Right Rail Chat Overlay */}
      <RightRailChat />
    </div>
  );
}
