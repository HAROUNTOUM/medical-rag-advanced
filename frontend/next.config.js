/** @type {import('next').NextConfig} */
module.exports = {
  output: "standalone",
  experimental: {
    outputFileTracingRoot: undefined,
    outputStandalone: true,
    skipMiddlewareUrlNormalize: true,
    skipTrailingSlashRedirect: true,
  },
  // Proxy all /api/v1/* requests to the FastAPI backend
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
    ];
  },
};
