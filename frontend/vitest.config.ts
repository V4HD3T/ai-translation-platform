// Separate from vite.config.ts on purpose: the build config stays exactly
// what production uses, and vitest brings its own vite internally (no
// version coupling with the app's Vite 8).
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    // Explicit include, because vitest's default glob is repo-wide and
    // happily collects e2e/*.spec.ts -- where Playwright's test() throws
    // "did not expect test() to be called here" and fails the run. The
    // two suites are different runners with different globals; only src
    // belongs to vitest.
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false, // class names aren't asserted on; queries go through roles/labels
  },
});
