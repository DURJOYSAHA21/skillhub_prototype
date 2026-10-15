# SkillHub - One Platform to Learn Every Skill

Full-stack implementation of the SkillHub platform from the AIUB SE project SRS
(77-page spec, 24 functional requirements), plus the SkillHub Match mentor-matching
engine, an in-app course concierge (SkillBot), notifications, wishlist & reviews,
and a global multi-language UI. Built with **FastAPI + PostgreSQL (SQLite fallback) + Next.js 14**.

The canonical product spec and full feature universe live in **docs/MASTER_PRD.md**.

## Highlights
- 24/24 SRS functional requirements implemented and covered by automated tests
- **Global multi-language**: English, Bangla, Hindi, Arabic, Spanish, French, Chinese, Indonesian - with RTL support
- Public **guest browsing** + category discovery (no login wall)
- Mentor course creation -> **admin approval** workflow (pending -> published/rejected)
- Enrollment: free (instant) or paid via a **simulated bank** flow, with PDF receipts
- Quizzes (timed, pass marks, attempts), assignments (file submission + grading), lesson notes
- Progress tracking (70% lessons / 30% quizzes) + **certificate PDF** on completion
- **SkillHub Match**: ranked mentors with match %, breakdown and reasons
- **SkillBot**: assistant that recommends courses, mentors and answers platform questions
- Role dashboards: learner / mentor / admin
- **Portable data layer**: PostgreSQL locally and on serverless (Vercel); file SQLite fallback for zero-config dev

## Tech stack
| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy, Pydantic, JWT, fpdf2 (certificate & receipt PDFs) |
| Database | PostgreSQL (psycopg2 driver); file SQLite fallback when `DATABASE_URL` is unset |
| Frontend | Next.js 14 (App Router), React 18, Tailwind |
| Deploy | Vercel (Next.js + a Python function mounted under `/api`) |

Local ports: backend `http://localhost:8030`, frontend `http://localhost:3030`.

## Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 18 (the bundled local cluster stores its data under the `pgdata` folder)

## Quick start (Windows)
Run these from the repo root (PowerShell):
- `run-postgres.cmd` - brings up the SkillHub PostgreSQL cluster on port 5433
- `run-backend.cmd` - creates the venv, installs deps, and runs uvicorn on http://localhost:8030 (seeds the DB on first run)
- `run-frontend.cmd` - installs npm deps and starts the dev server on http://localhost:3030

Then open http://localhost:3030 in a browser.

### How the backend finds the database
`backend/app/db.py` reads the `DATABASE_URL` environment variable:
- For local dev it auto-loads **`backend/.env`** (git-ignored), which points at the bundled cluster (`postgresql://skillhub@127.0.0.1:5433/skillhub`).
- A bare `postgresql://` URL is auto-switched to the `psycopg2` driver.
- With no `DATABASE_URL` set, the app falls back to a file SQLite database (`backend/skillhub.db`) so it still runs with zero configuration.
- The schema is created and seeded automatically on first backend startup.

## Demo accounts (seeded)
| Role | Email | Password |
|---|---|---|
| Admin | admin@skillhub.dev | Admin123 |
| Mentor | rifat@skillhub.dev | Mentor123 |
| Learner | learner@skillhub.dev | Learner123 |

## SRS requirement coverage (all 24)
1. Signup with name/email/BD 11-digit phone/role + strong password rules
2. Email OTP verification activates the account (dev OTP surfaced in API for testing)
3. Login with lockout after 5 failed attempts (30 min); status unverified/active/blocked
4. Forgot password via OTP + change password from profile
5. Profile view/edit (name, phone, DOB, country, bio, language, picture)
6. Course creation by mentors -> admin approval -> published
7. Lessons with file upload (served from /files/)
8. Enrollment: free instant, paid via simulated bank (card 12-19 digits, PIN, bank OTP)
9. Quizzes: timed, passing score, max attempts, per-question review
10. Assignments: file submission + drafts, mentor grading
11. Progress tracking (70% lessons / 30% quizzes) + certificate PDF on completion
12. 1:1 chat learner <-> mentor with attachments (polling)
13. Multi-language UI across 8 languages with RTL, persisted per user (PUT /auth/profile)
14. Search + filters (keyword, category, language, max price, min rating)
15. SkillHub Match: ranked mentor list with match percent, breakdown, reasons
16. Admin course approval queue (publish/reject/feature)
17. Admin transaction log (status/date filters, revenue total) + refunds
18. Mentor transaction view + total earned
19. Learner transaction history + PDF receipts (SH-YYYYMMDD-XXXX refs)
20. User management: block, unblock, role change, permanent removal (admins protected)
21. Payment method management (add, enable/disable - UCB/BRAC/City/bKash seeded)
22. Admin analytics: users by role, courses by status, enrollments, revenue, top courses
23. Role dashboards: learner hub / mentor studio / admin console (/dashboard)
24. Platform landing + guest browse of published courses (no login wall)

Plus product extras beyond the SRS: notifications center, wishlist, course reviews
(with mentor replies), lesson notes, learner goals, and the SkillBot concierge.

## API map
The FastAPI app mounts routers at the root (except `auth` and `admin`). Health: `GET /api/health` and `GET /health`.

- **Auth** - `/auth`: `signup`, `verify`, `login`, `forgot`, `forgot-confirm`, `change-password`, `me`, `profile`, `picture`
- **Courses** - `/courses`, `/courses/{id}`, nested `lessons`, `quizzes`, `assignments`, `thumbnail`, `resubmit`, quiz `publish`
- **Learning & assessment** - `/courses/{id}/learn`, `/lessons/{id}/complete`, `/quizzes/{id}` (+ `submit`), `/assignments/{id}/submit` (+ `submissions`), `/courses/{id}/certificate`, `/my/courses`
- **Enrollment & payments** - `/enroll/free`, `/pay/start`, `/pay/confirm`, `/txns/me`, `/txns/mentor`, `/txns/admin`, `/txns/{id}/receipt`
- **Chat** - `/chat/threads`, `/chat/{peer_id}` (history + send, `since_id` polling, file attachments)
- **Match** - `/match`, `/meta`, `/skills/resolve`, `/mentors/{id}`
- **Mentor studio** - `/mentor/overview`, `/mentor/profile`, `/courses/{id}/students`, `/quizzes/{id}/results`, grade submissions, reorder lessons, reply to reviews
- **Learner hub** - `/learner/overview`, `/my/certificates`, `/my/results`, `/my/notes`, `/my/goals`, lesson notes, cancel enrollment
- **Product** - `/notifications` (+ mark read / read-all), `/wishlist`, `/courses/{id}/reviews`
- **SkillBot** - `/bot/ask`, `/bot/starters`
- **Admin** - `/admin`: users (status/role/unlock/remove), courses (approve/feature/remove), categories, payment-methods, reviews, enrollments, refunds, broadcast, export, analytics, mentor verification
- **Files** - `/files/{name}` (uploaded lesson/material assets)

## Project structure
- `backend/app/` - `main.py`, `db.py` (models + portable engine), `security.py` (JWT/hashing), `deps.py`, `engine.py` (SkillHub Match), `reports.py` (PDF cert/receipt)
- `backend/app/routers/` - `auth`, `courses`, `enroll`, `assess`, `chat`, `admin`, `match`, `mentor`, `learner`, `product`, `bot`
- `backend/tests/` - `test_api.py`, `test_engine.py`, `test_product.py`
- `frontend/app/` - landing + `browse`, `course`, `learn`, `match`, `chat`, `dashboard`, `mentor`, `profile`, `login`, `signup`, `forgot`
- `frontend/components/` - `Nav`, `LangContext`, `Chatbot`, `LearnerHub`, `MentorStudio`, `AdminConsole`, `AssessBuilder`, `TxnTable`, `ui`
- `frontend/lib/` - `api.js`, `i18n.js` (8-language dictionaries)
- `frontend/api/` - serverless entry (`index.py`) that runs the FastAPI app on Vercel
- `docs/MASTER_PRD.md` - full product spec and feature universe
- `pgdata/` - local PostgreSQL cluster data (git-ignored)

## Testing
From `backend/`, using the venv Python:
- `.venv\Scripts\python -m pytest tests -q`
- Tests default to SQLite; set `DATABASE_URL` first to run them against PostgreSQL.

## Deployment (Vercel)
- `frontend/` is a Next.js app deployed to Vercel; the FastAPI backend runs as a serverless Python function mounted at `/api` (`frontend/api/index.py`, with `frontend/vercel.json` rewriting `/api/*`).
- Set `DATABASE_URL` in the Vercel project environment variables to a managed Postgres (Vercel Postgres, Neon, etc.). Because state lives in Postgres, data survives serverless cold starts.
- The local `backend/.env` and `pgdata/` are git-ignored and never deployed.
- After deploy, `GET /api/health` should return `{ "ok": true, "users": N, "courses": N }` (the landing page shows these as public social proof).


## Production configuration & security
SkillHub has one switch for public use: set `SKILLHUB_ENV=production`. That turns on:
- **Mandatory JWT secret** - the app refuses to start unless `SKILLHUB_SECRET` is a 32+ char random value (no more forgeable default tokens).
- **Real email OTP** - codes are only emailed (via `SMTP_*`); the `dev_otp` field is no longer returned. In production the app refuses to start if SMTP is missing, unless you deliberately set `SKILLHUB_ALLOW_DEV_OTP=1` for a private demo.
- **Rate limiting** - per-IP limits on login/signup/verify/forgot/password-change/payment (HTTP 429 when exceeded).
- **CORS lockdown** - set `SKILLHUB_ORIGINS` to your frontend origin(s); unset means allow-all (dev convenience only).

Full variable reference lives in **`backend/.env.example`** - copy it to `backend/.env` for local dev and set the same keys in Vercel.

### Still needed before a real public launch
- **Object storage for uploads**: on serverless the local disk is ephemeral, so lesson/picture uploads do not persist. Mount a persistent volume (Render/Railway/Fly) or front uploads with S3 / Vercel Blob before exposing course materials publicly.
- **Real payments**: the bank/OTP flow is a simulation (no money moves). Wire a gateway (Stripe / bKash / SSLCommerz) to actually charge.
- **TLS + managed Postgres**: deploy against a managed database with `?sslmode=require`.

### Security posture (unchanged)
- Passwords: PBKDF2-HMAC-SHA256, 120k rounds. Sessions: HS256 JWT carrying only user id + role (12h expiry).
- Blocked users get 403 on every authenticated endpoint; new mentor courses default to `pending` for admin approval.
## Notes & design
- JWT carries only the user id + role (12 h expiry); password hashes never leave the backend.
- Payment and OTP flows are simulations (no real money or email) per SRS dev constraints.
- Blocked users receive `403` at every authenticated endpoint.
- New mentor courses are created with status `pending` and notify admins for approval.
- UI strings live in `frontend/lib/i18n.js`; Arabic renders right-to-left.