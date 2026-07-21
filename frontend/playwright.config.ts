import { defineConfig } from "@playwright/test";

// E2E against the REAL stack: Playwright boots the actual FastAPI backend
// (fresh throwaway SQLite + seeded content) and the Vite dev server, then
// drives a real Chromium through the full learner journey. Selectors lean
// on the v0.1.1 accessibility work (labels, roles, fieldset legends) --
// the a11y round paying for itself as testability.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "on-first-retry",
    // Escape hatch for environments where `npx playwright install` is
    // blocked (restricted network egress) but a compatible Chromium is
    // already on disk:
    //   E2E_CHROMIUM_PATH=/path/to/chrome npm run test:e2e
    // Unset everywhere else, so CI uses the version Playwright manages.
    launchOptions: process.env.E2E_CHROMIUM_PATH
      ? { executablePath: process.env.E2E_CHROMIUM_PATH }
      : undefined,
  },
  // Both servers bind explicitly to 127.0.0.1 rather than relying on the
  // default "localhost". That is not cosmetic: on a host with IPv6 (every
  // GitHub Actions runner; not this project's dev sandbox, which is why it
  // passed locally and timed out in CI), "localhost" can resolve to ::1
  // first, so the server listens on [::1]:5173 while Playwright polls
  // http://127.0.0.1:5173 and waits out the full timeout. Pinning both the
  // bind address and the polled URL to the same literal removes the
  // ambiguity entirely.
  //
  // stdout/stderr are piped so a future startup failure shows *why* in the
  // job log instead of only "Timed out waiting 60000ms".
  webServer: [
    {
      // rm first: each run starts from the seeded state, so quiz answers
      // and adaptive behaviour stay deterministic.
      command:
        "rm -f /tmp/lingua-e2e.db && cd ../backend && DATABASE_URL=sqlite:////tmp/lingua-e2e.db " +
        "uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: false,
      // Generous: a cold CI runner pays for Alembic migrations here, and a
      // timeout that's merely tight looks exactly like a real failure.
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
      // Vite pre-bundles dependencies on a cold node_modules/.vite cache,
      // which is exactly the CI case.
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
  ],
});
