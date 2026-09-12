/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  basePath: '/mpgroundwatermonitor',
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000",
  },
  trailingSlash: true,
};
module.exports = nextConfig;
