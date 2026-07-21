import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      includeAssets: ["apple-touch-icon.png", "favicon-32.png"],
      manifest: {
        name: "Lingua — AI Translation and Language Learning",
        short_name: "Lingua",
        description:
          "Translate text, study courses, and practise vocabulary with spaced repetition.",
        theme_color: "#171d33",
        background_color: "#f6f7fb",
        display: "standalone",
        start_url: "/",
        scope: "/",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
          // Separate maskable entry with a 20% safe zone: Android crops
          // icons to its own shape and would otherwise clip the glyph.
          {
            src: "icon-maskable-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        // Precache the app shell only. API responses are deliberately NOT
        // cached here: translation history, quiz sessions, and streaks are
        // per-user and time-sensitive, and a stale-served quiz session
        // would break the v0.0.9 served-set grading contract. The Redis
        // layer already handles the one thing worth caching (repeat
        // translations) server-side, where invalidation is manageable.
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
        // Any navigation falls back to the shell, matching the nginx and
        // Vercel SPA rewrites -- except /health and anything API-shaped.
        navigateFallback: "index.html",
        navigateFallbackDenylist: [/^\/health/, /^\/api/],
        cleanupOutdatedCaches: true,
      },
      devOptions: {
        // Service workers stay off in dev: a stale SW is a genuinely
        // confusing debugging experience, and `npm run dev` should always
        // serve exactly what's on disk.
        enabled: false,
      },
    }),
  ],
  server: {
    port: 5173,
  },
});
