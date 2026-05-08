import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Approvals } from './pages/Approvals';
import { Integrations } from './pages/Integrations';
import { OAuthCallback } from './pages/OAuthCallback';
import { Settings } from './pages/Settings';
import { Programs } from './pages/Programs';
import { ProgramDetails } from './pages/ProgramDetails';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/programs" replace />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="programs" element={<Programs />} />
          <Route path="programs/:id" element={<ProgramDetails />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="oauth/callback" element={<OAuthCallback />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
