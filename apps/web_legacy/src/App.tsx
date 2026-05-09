import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Chat } from './pages/Chat';
import { ProgramsHierarchy } from './pages/ProgramsHierarchy';
import { Approvals } from './pages/Approvals';
import { Inbox } from './pages/Inbox';
import { Settings } from './pages/Settings';

// Obsolete or remaining pages
import { Integrations } from './pages/Integrations';
import { OAuthCallback } from './pages/OAuthCallback';
import { Programs } from './pages/Programs';
import { ProgramDetails } from './pages/ProgramDetails';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Default redirect to Home Dashboard */}
          <Route index element={<Navigate to="/home" replace />} />
          
          {/* New Core Redesign Routes */}
          <Route path="home" element={<Home />} />
          <Route path="chat" element={<Chat />} />
          <Route path="programs" element={<ProgramsHierarchy />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="inbox" element={<Inbox />} />
          <Route path="settings" element={<Settings />} />

          {/* Legacy or Auth Routes */}
          <Route path="oauth/callback" element={<OAuthCallback />} />
          <Route path="integrations" element={<Integrations />} />
          
          {/* Fallback for old program detail links if any exist in the wild */}
          <Route path="programs/legacy" element={<Programs />} />
          <Route path="programs/legacy/:id" element={<ProgramDetails />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
