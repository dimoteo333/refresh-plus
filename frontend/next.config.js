/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost', 'firebasestorage.googleapis.com', 'shbimg.interparkb2b.co.kr', 'refresh-plus-production.up.railway.app', 'refresh-plus.vercel.app'],
  },
}

module.exports = nextConfig
