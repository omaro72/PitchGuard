import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    tsconfigPaths: true,
  },
  test: {
    environment: "jsdom",
    pool: "threads",
    restoreMocks: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
