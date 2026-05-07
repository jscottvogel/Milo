import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Chat } from './pages/Chat';
import { Approvals } from './pages/Approvals';
import { Integrations } from './pages/Integrations';
import { OAuthCallback } from './pages/OAuthCallback';

function Placeholder({ title }: { title: string }) {
  return (
    <div className="flex h-full items-center justify-center z-10 animate-fade-in">
      <h2 className="text-2xl font-semibold text-muted-foreground">{title} - Coming Soon</h2>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Chat />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="programs" element={<Placeholder title="Programs" />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="oauth/callback" element={<OAuthCallback />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
