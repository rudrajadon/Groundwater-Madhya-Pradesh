/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // No basePath - portfolio at root, groundwater at /mpgroundwatermonitor
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000",
    NEXT_PUBLIC_BASE_PATH: '',
  },
  trailingSlash: true,
};
module.exports = nextConfig;
