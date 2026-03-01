import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable Turbopack for this build (use webpack instead)
  // Turbopack has issues with child_process spawn
};

export default nextConfig;
