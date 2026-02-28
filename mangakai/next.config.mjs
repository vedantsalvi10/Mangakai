import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use this app directory as root so Next doesn't get confused by the parent's package-lock.json
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
