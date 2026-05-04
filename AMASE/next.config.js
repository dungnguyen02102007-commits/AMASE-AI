/** @type {import('next').NextConfig} */
const nextConfig = {
  // Explicit empty turbopack config tells Next.js 16 the webpack config below is intentional.
  turbopack: {},
  // @react-pdf/renderer → pdfkit/fontkit reference Node built-ins that don't
  // exist in the browser bundle. Stub them out when building with --webpack.
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        stream: false,
        zlib: false,
        crypto: false,
        buffer: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
