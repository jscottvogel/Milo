import { NavLink, Outlet } from 'react-router-dom';
import { MessageSquare, CheckCircle, Package, Blocks } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { path: '/', icon: MessageSquare, label: 'Chat' },
  { path: '/approvals', icon: CheckCircle, label: 'Approvals' },
  { path: '/programs', icon: Package, label: 'Programs' },
  { path: '/integrations', icon: Blocks, label: 'Integrations' },
];

export function Layout() {
  return (
    <div className="flex h-screen bg-background text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 glass flex flex-col z-10 border-r border-border">
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-400">
            Milo
          </h1>
          <p className="text-xs text-muted-foreground mt-1 tracking-wider uppercase">Agent Workspace</p>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative',
                  isActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:bg-white/5 hover:text-white'
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <div className="absolute left-0 w-1 h-5 bg-primary rounded-r-full shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
                  )}
                  <item.icon className={clsx("w-5 h-5", isActive ? "text-primary" : "group-hover:text-white")} />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        
        {/* User profile mock */}
        <div className="p-4 border-t border-border/50">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-sm shadow-lg">
              JS
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">Dev User</p>
              <p className="text-xs text-muted-foreground truncate">Admin</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-gradient-to-br from-background to-[#111115]">
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary/10 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-10 left-1/4 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none"></div>
        
        <Outlet />
      </main>
    </div>
  );
}
