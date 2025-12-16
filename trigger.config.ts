import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "proj_revxyohjfwmzenuqomth",
  // Node.js runtime for Vercel AI SDK v5 jobs
  // Python agent calls these jobs via Trigger.dev API (not as Trigger jobs)
  runtime: "node",
  // Only Node.js job directory
  dirs: ["./trigger"],
  maxDuration: 10,
  retries: {
    enabledInDev: true,
    default: {
      maxAttempts: 3,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 10000,
      factor: 2,
    },
  },
});

