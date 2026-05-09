import { useEffect, useState } from 'react';
import { Blocks, Mail, Plus, Check } from 'lucide-react';
import { generateCodeVerifier, generateCodeChallenge } from '../utils/oauth';
import { apiFetch } from '../api/client';

// Mock Config
const GOOGLE_CLIENT_ID = 'mock-client-id.apps.googleusercontent.com';
const REDIRECT_URI = window.location.origin + '/oauth/callback';
const SCOPE = 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send';

export function Integrations() {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch current integrations status
    apiFetch<any[]>('/v1/integrations')
      .then(data => {
        setIsConnected(data.some((i: any) => i.provider === 'gmail' && i.status === 'connected'));
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const handleConnectGmail = async () => {
    const verifier = generateCodeVerifier();
    sessionStorage.setItem('gmail_code_verifier', verifier);
    const challenge = await generateCodeChallenge(verifier);

    // Google OAuth URL construction
    const params = new URLSearchParams({
      client_id: GOOGLE_CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      response_type: 'code',
      scope: SCOPE,
      code_challenge: challenge,
      code_challenge_method: 'S256',
      access_type: 'offline',
      prompt: 'consent'
    });

    // In a real app, we redirect to Google:
    // window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    console.debug("Mock Google OAuth Params:", params.toString());
    
    // For PoC without a real client ID, we'll just redirect locally with a mock code:
    window.location.href = `${REDIRECT_URI}?code=mock_auth_code_from_google&state=mock_state`;
  };

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto p-8 z-10 overflow-y-auto scrollbar-hide">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
          <Blocks className="text-primary" size={32} />
          Integrations
        </h2>
        <p className="text-muted-foreground mt-2">Connect Milo to your external services to enable autonomous workflows.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 flex flex-col items-center justify-center text-center animate-fade-in relative overflow-hidden">
          <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
            <Mail size={32} className="text-red-400" />
          </div>
          <h3 className="text-xl font-medium text-white mb-2">Google Workspace</h3>
          <p className="text-sm text-muted-foreground mb-6">Enable Milo to draft emails, read threads, and manage your calendar natively.</p>
          
          {isLoading ? (
            <div className="h-10 w-full animate-pulse bg-white/10 rounded-xl"></div>
          ) : isConnected ? (
            <button disabled className="w-full py-2.5 px-4 rounded-xl bg-green-500/20 text-green-400 font-medium flex items-center justify-center gap-2 border border-green-500/30">
              <Check size={18} />
              Connected
            </button>
          ) : (
            <button 
              onClick={handleConnectGmail}
              className="w-full py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white font-medium flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_20px_rgba(59,130,246,0.5)]"
            >
              <Plus size={18} />
              Connect Gmail
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
