# Lingua — AI Translation and Language Learning Platform

**Version:** 0.0.4

A platform offering real-time translation and interactive language
learning for multilingual users. Built as part of a university graduation
project.

For the full architecture, technology rationale, and roadmap, see
**[ARCHITECTURE.md](./ARCHITECTURE.md)**. For the complete version history,
see **[CHANGELOG.md](./CHANGELOG.md)**.

## What's new in 0.0.4

- **Automatic language detection** — an opt-in "Detect language" option on
  the translate page (`POST /detect-language`).
- **Text-to-speech** — a speaker button reads translations and vocabulary
  words aloud, browser-based, no server round-trip.
- **Spaced repetition** — a real SM-2 algorithm behind a new `/review`
  flashcard flow (`GET /users/me/review-queue`, `POST
  /vocabulary/{id}/review`).
- Backend: 51/51 tests passing (24 new this version).

Full details, including honest notes on where automatic language detection
is and isn't reliable: `CHANGELOG.md`.

## Quick start

You'll need two terminals — one for the backend, one for the frontend.

**Terminal 1 — Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
→ http://localhost:8000 (Swagger: http://localhost:8000/docs)

**Terminal 2 — Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
→ http://localhost:5173

See `backend/README.md` and `frontend/README.md` for detailed instructions
and architecture notes.

## Status

- ✅ Backend: auth, translation, courses/lessons/vocabulary, quizzes, progress/streak, language detection, spaced repetition — 51 tests passing
- ✅ Frontend: a working interface for every flow (React + TypeScript)
- ✅ Speech: voice input (translation + pronunciation practice) and voice output (translations + vocabulary), both browser-based, no model download
- ✅ Progress tracking: daily streak, per-course completion percentage (`/progress`)
- ✅ Spaced repetition: SM-2-scheduled vocabulary review (`/review`)
- ⏳ Up next: the real NLLB model (needs to be set up locally), content expansion, end-to-end testing

(Full roadmap: `ARCHITECTURE.md` §6 · Full version history: `CHANGELOG.md`)
