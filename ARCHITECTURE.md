# AI-Based Automatic Translation and Language Learning Platform

**Version:** 0.0.2

An integrated platform offering real-time translation and interactive
language learning (quizzes + vocabulary) for multilingual users.

## 1. Scope

- Transformer-based translation engine (NLLB-200 — 200+ languages, single model)
- Interactive quiz system (multiple choice, automatic scoring)
- Course → lesson → vocabulary hierarchy
- User accounts, session management (JWT), translation history

## 2. Architecture

```
Client (Web)   →   API server (FastAPI)   →   ┬→ NLLB translation model
React                                          └→ Database
                                               (user, course, quiz, history)
```

- **Client**: React + TypeScript.
- **API server**: FastAPI. Serves authentication, translation, and
  course/lesson/quiz endpoints over REST. Real-time translation works by
  having the client send a debounced (350-500ms) request while typing.
- **Translation engine**: `facebook/nllb-200-distilled-600M`. A single
  model covers 200+ languages.
- **Database**: SQLite in development; switching to PostgreSQL in
  production is a one-line change (`DATABASE_URL`), since the access layer
  is abstracted through SQLModel.

## 3. Technology choices and rationale

| Layer | Choice | Why |
|---|---|---|
| Backend | Python + FastAPI | Async support, automatic OpenAPI/Swagger docs, type safety (Pydantic) |
| ORM | SQLModel | Combines SQLAlchemy + Pydantic — the same class doubles as table and schema |
| Translation | HuggingFace `transformers` + NLLB-200 | Open source, free, directly satisfies the "transformer-based model" requirement |
| Authentication | JWT (python-jose) + bcrypt | Stateless, works unchanged if a mobile client is added later |
| Frontend | React + TypeScript | Matches existing experience, large ecosystem |

## 4. Data model (summary)

- `User` — user account, native language
- `Language` — supported languages (code + name)
- `TranslationHistory` — the user's past translations
- `Course` → `Lesson` → `VocabularyItem` — learning content hierarchy
- `Quiz` → `QuizQuestion`, `QuizAttempt` — quiz questions and user attempts

See `backend/app/models.py` for the full field list.

## 5. Completed so far

**Phase 0 — Backend skeleton** ✅

- Register / login / JWT-protected endpoints (`/auth/*`)
- Real-time translation, anonymous + registered use, history saving (`/translate*`)
- Course → lesson → vocabulary endpoints (`/courses*`, `/lessons/*`)
- Quiz retrieval (both `/quizzes/{id}` and `/lessons/{id}/quiz`) + automatic scoring
- Clean abstraction between the mock translation service (for development
  without downloading a model) and the real NLLB service (one setting flips
  it on)

**Phase 2 — Frontend** ✅

- React + TypeScript, via Vite. Product name: **Lingua**.
- Pages: real-time translation, login/register, course list → lesson list
  → vocabulary → quiz flow, translation history.
- A dedicated design token system (`src/styles/tokens.css`).

See `backend/README.md` and `frontend/README.md` for setup and run
instructions.

## 6. Roadmap

| Phase | Content |
|---|---|
| 0 | ✅ Done — Architecture design, backend skeleton, test suite |
| 2 | ✅ Done — Frontend: translation UI, course/lesson flow, quiz UI |
| 3 | Speech recognition / pronunciation practice |
| 4 | Progress tracking, streak system |
| 1 | Real NLLB model integration |
| 5 | End-to-end testing, usability evaluation |
| 6 | Project report, documentation, defense presentation |

## 7. Next step

Speech recognition, progress tracking, or real NLLB integration — which
one?
