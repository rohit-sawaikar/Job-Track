import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const rawBackendUrl = process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000";
    const baseUrl = rawBackendUrl.replace(/\/+$/, "").replace(/\/api\/py$/, "");
    return [
      {
        source: "/api/py/:path*",
        destination: `${baseUrl}/api/py/:path*`,
      },
    ];
  },
};

export default nextConfig;

