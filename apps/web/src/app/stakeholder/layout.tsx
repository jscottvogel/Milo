import { ReactNode } from 'react';

export default function StakeholderLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white flex flex-col">
      <header className="border-b border-white/10 p-4 flex justify-between items-center bg-[#0d0d12]">
        <div className="font-bold text-xl tracking-tight text-white/90">
          Milo <span className="text-white/40 font-normal">Stakeholder Portal</span>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-white/60">Help</div>
          <div className="h-8 w-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-semibold text-sm">
            SH
          </div>
        </div>
      </header>
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
