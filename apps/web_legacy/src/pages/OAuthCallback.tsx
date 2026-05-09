import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { apiFetch } from '../api/client';

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const verifier = sessionStorage.getItem('gmail_code_verifier');

    if (!code) {
      setStatus('error');
      setErrorMessage('No authorization code found in URL.');
      return;
    }

    // We mocked the redirect for the PoC, so verifier might be present if they clicked the button.
    
    apiFetch('/v1/integrations/oauth/callback', {
      method: 'POST',
      body: JSON.stringify({
        code,
        code_verifier: verifier || 'mock_verifier',
        provider: 'gmail'
      })
    })
    .then(() => {
      setStatus('success');
      setTimeout(() => navigate('/integrations'), 2000);
    })
    .catch(err => {
      setStatus('error');
      setErrorMessage(err.message);
    });

  }, [searchParams, navigate]);

  return (
    <div className="flex flex-col h-full w-full items-center justify-center z-10 animate-fade-in p-8">
      <div className="glass-card p-10 flex flex-col items-center text-center max-w-md w-full">
        {status === 'loading' && (
          <>
            <Loader2 className="animate-spin text-primary w-16 h-16 mb-6" />
            <h2 className="text-2xl font-bold text-white mb-2">Connecting...</h2>
            <p className="text-muted-foreground">Securing your integration with Milo.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mb-6">
              <CheckCircle className="text-green-500 w-10 h-10" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Connected!</h2>
            <p className="text-muted-foreground">Your account has been successfully linked. Redirecting...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-6">
              <XCircle className="text-red-500 w-10 h-10" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Connection Failed</h2>
            <p className="text-muted-foreground mb-6">{errorMessage}</p>
            <button 
              onClick={() => navigate('/integrations')}
              className="px-6 py-2.5 rounded-xl bg-surface border border-white/10 hover:bg-white/5 transition-colors"
            >
              Return to Integrations
            </button>
          </>
        )}
      </div>
    </div>
  );
}
