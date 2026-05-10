import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow connections from the local network / Tailscale IP for testing
  allowedDevOrigins: ['100.64.100.6', 'localhost'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
