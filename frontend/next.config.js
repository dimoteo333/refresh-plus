/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost', 'firebasestorage.googleapis.com', 'shbimg.interparkb2b.co.kr'],
  },
}

module.exports = nextConfig
