# Frontend — Lingua

**Version:** 0.0.2

A single-page app built with Vite + React + TypeScript. Consumes the
backend's authentication, translation, and course/lesson/vocabulary/quiz
endpoints.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
```

`VITE_API_URL` in `.env` points to where the backend is running (default:
`http://localhost:8000`).

## Running

The backend needs to already be running in a separate terminal (see
`../backend/README.md`). Then:

```bash
npm run dev
```

The app opens at http://localhost:5173.

## Production build

```bash
npm run build     # type-checking + build into dist/
npm run preview   # serves the built version locally
```

## Site map

| Path | Description |
|---|---|
| `/` | Real-time translation (no login required) |
| `/login`, `/register` | Authentication |
| `/courses` | Course list |
| `/courses/:courseId` | Course detail + lesson list |
| `/lessons/:lessonId` | Vocabulary + entry point to the quiz |
| `/lessons/:lessonId/quiz` | Taking the quiz (requires login) |
| `/history` | Translation history (requires login) |

## Architecture notes

- **`src/api/`** — a thin client layer that mirrors the backend endpoints.
  Every request goes through `api/client.ts` (token attachment and error
  normalization live in one place).
- **`src/context/AuthContext.tsx`** — keeps the JWT in `localStorage` and
  verifies it against `/auth/me` on load.
- **Design tokens** live in one place, `src/styles/tokens.css` (color,
  typography, spacing scale) — use those variables when adding new
  components.
- Every page ships with its own CSS Modules file (`Page.module.css`) — no
  risk of global class name collisions.

## Known warning

`npm audit` reports a moderate-severity advisory about the `esbuild`
dependency in Vite's dev server (only during `npm run dev`, doesn't affect
the production build). Fixing it requires a breaking upgrade to Vite 8;
deliberately deferred for now. Details:
https://github.com/advisories/GHSA-67mh-4wv8-2f99
