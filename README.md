# SkillHub: One Platform to Learn Every Skill

A full-stack online learning marketplace where **mentors** publish courses,
**learners** find, buy and complete them in their own language, and an
**admin** approves courses and runs the platform. It includes **SkillHub Match**,
a mentor-matching engine that explains its ranking, and **SkillBot**, an in-app
assistant that answers from the platform's real data.

Built with **FastAPI + PostgreSQL + Next.js 14**, from the 77-page SRS of an
AIUB Software Engineering project (24 functional requirements, all implemented).

**Live demo: <https://skillhubprototype-frontend.vercel.app>**

![SkillHub landing page](docs/screenshots/01-landing.png)

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Learner | learner@skillhub.dev | Learner123 |
| Mentor | rifat@skillhub.dev | Mentor123 |
| Admin | admin@skillhub.dev | Admin123 |

Payments and bank OTPs are simulated: no real money moves.

---

## Features

| Role | What they can do |
|---|---|
| **Everyone** | Browse the course catalogue without an account · search and filter by keyword, category, language, level, price and rating · use the UI in **8 languages** (English, Bangla, Hindi, Arabic, Spanish, French, Chinese, Indonesian) with **right-to-left** layout for Arabic · ask SkillBot |
| **Learner** | Sign up with email OTP · enroll free or pay through a simulated bank flow · PDF receipts · lessons, timed quizzes and assignments · progress tracking and a **PDF certificate** on completion · wishlist, reviews, lesson notes and learning goals · notifications · 1:1 chat with mentors · **SkillHub Match** to find a mentor |
| **Mentor** | Mentor Studio: create courses (sent to the admin for approval), upload lessons, build quizzes and assignments, grade submissions, see students, reply to reviews, track earnings |
| **Admin** | Admin Console: approve, reject or feature courses · block, unblock or change users' roles · transactions and refunds · payment methods · review moderation · categories · announcements · analytics · CSV exports |

## Screenshots

| Course catalogue (filters) | Course page |
|---|---|
| ![Browse](docs/screenshots/02-browse.png) | ![Course](docs/screenshots/03-course.png) |
| **SkillHub Match: ranked mentors with reasons** | **SkillBot answers from live data** |
| ![Match](docs/screenshots/04-match.png) | ![SkillBot](docs/screenshots/09-skillbot.png) |
| **Learner Hub** | **Mentor Studio** |
| ![Learner hub](docs/screenshots/05-learner-hub.png) | ![Mentor studio](docs/screenshots/06-mentor-studio.png) |
| **Admin Console: course approval queue** | **Arabic, right-to-left** |
| ![Admin](docs/screenshots/07-admin-console.png) | ![Arabic RTL](docs/screenshots/08-arabic-rtl.png) |

## How SkillHub Match ranks mentors

`backend/app/engine.py` is pure Python with no database code, so it can be unit
tested on its own. For a skill and the learner's languages in order of
preference, each mentor gets a score and a breakdown that explains it:

| Part | Weight | Built from |
|---|---|---|
| Skill | 45 % | teaching depth (1–5) and years of experience |
| Language | 30 % | the mentor's fluency in each of the learner's languages; the first choice counts most |
| Quality | 25 % | rating, reply time and course-completion rate |

Free text is resolved to a known skill first ("python" → *Python Programming*,
via aliases), and every result lists its reasons (for example "Depth L4/5 with
5 yrs teaching", "Rated 4.7 by 240 learners").

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Pydantic, JWT, fpdf2 (certificate and receipt PDFs) |
| Database | PostgreSQL (psycopg2); falls back to a SQLite file when `DATABASE_URL` isn't set |
| Frontend | Next.js 14 (App Router), React 18, Tailwind CSS |
| Tests | pytest + httpx (23 tests: API flows, match engine, product features) |
| Hosting | Vercel: the Next.js app plus the FastAPI app as a Python service under `/api` |

## Architecture

```mermaid
flowchart LR
    B[Browser] --> N[Next.js 14 pages<br/>frontend/app]
    N -->|fetch /api/*| F[FastAPI<br/>routers]
    F --> E[SkillHub Match engine]
    F --> P[PDF reports<br/>certificates, receipts]
    F -->|SQLAlchemy| DB[(PostgreSQL<br/>or SQLite)]
```

On Vercel, `frontend/vercel.json` sends `/api/*` to the Python service and
everything else to Next.js, so the whole app runs on one domain.
`frontend/api/app/` is a copy of `backend/app/` packaged for that service.

## Run it locally

You need **Python 3.10+** and **Node.js 18+**. PostgreSQL is optional: with no
`DATABASE_URL`, the backend creates and seeds a SQLite file (`backend/skillhub.db`)
on first start.

```bash
# 1. Backend: http://localhost:8030
cd backend
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8030 --reload

# 2. Frontend: http://localhost:3030 (in a second terminal)
cd frontend
npm install
npm run dev
```

Open <http://localhost:3030> and log in with a demo account above.

On Windows, `run-backend.cmd` and `run-frontend.cmd` do the same steps.
To use PostgreSQL instead of SQLite, set `DATABASE_URL`
(for example `postgresql://user:password@localhost:5432/skillhub`) or put it in
`backend/.env`. The schema and demo data are created on first start.

## Tests

```bash
cd backend
python -m pytest tests -q
```

The tests use SQLite by default. Set `DATABASE_URL` first to run them against PostgreSQL.

## Security

| Area | How it's handled |
|---|---|
| Passwords | PBKDF2-HMAC-SHA256, 120,000 rounds, random salt; strong-password rules at sign-up |
| Sessions | HS256 JWT holding only the user id and role, 12-hour expiry |
| Login | account locked for 30 minutes after 5 failed attempts; email OTP to verify accounts and reset passwords |
| Access control | admin and mentor endpoints check the user's role (`403` otherwise); blocked users get `403` on every logged-in endpoint; new courses stay `pending` until an admin approves them |
| Production mode | `SKILLHUB_ENV=production` refuses to start without a 32+ character JWT secret and SMTP, stops returning the dev OTP, turns on per-IP rate limits (HTTP 429) for login, sign-up, OTP, password and payment endpoints, and `SKILLHUB_ORIGINS` limits CORS |

All settings are listed in [`backend/.env.example`](backend/.env.example).

## Known limitations

- **Payments are simulated.** A real gateway (Stripe, bKash, SSLCommerz) would be the next step.
- **Uploads don't persist on Vercel.** Serverless disks are temporary, so
  uploaded lesson files and pictures disappear between deploys. They need
  object storage (S3 or Vercel Blob) for real use.
- **The live demo is shared.** Everyone uses the same demo accounts, so its data can change.

<details>
<summary><b>All 24 SRS requirements</b></summary>

1. Sign-up with name, email, Bangladeshi 11-digit phone, role and strong-password rules
2. Email OTP verification activates the account
3. Login with a 30-minute lockout after 5 failed attempts; status unverified / active / blocked
4. Forgot password via OTP, and change password from the profile
5. Profile view and edit (name, phone, date of birth, country, bio, language, picture)
6. Course creation by mentors → admin approval → published
7. Lessons with file upload
8. Enrollment: free (instant) or paid through a simulated bank (card 12–19 digits, PIN, bank OTP)
9. Quizzes: timed, passing score, maximum attempts, per-question review
10. Assignments: file submission and drafts, mentor grading
11. Progress tracking (70 % lessons, 30 % quizzes) and a PDF certificate on completion
12. 1:1 learner–mentor chat with attachments
13. Multi-language UI (8 languages, Arabic right-to-left), saved per user
14. Search and filters (keyword, category, language, maximum price, minimum rating)
15. SkillHub Match: ranked mentors with match percentage, breakdown and reasons
16. Admin course approval queue (publish, reject, feature)
17. Admin transaction log (status and date filters, revenue total) and refunds
18. Mentor transactions and total earned
19. Learner transaction history and PDF receipts (`SH-YYYYMMDD-XXXX` references)
20. User management: block, unblock, change role, remove (admins protected)
21. Payment methods: add, enable, disable (UCB, BRAC, City Bank, bKash seeded)
22. Admin analytics: users by role, courses by status, enrollments, revenue, top courses
23. Role dashboards: Learner Hub, Mentor Studio, Admin Console
24. Public landing page and catalogue for guests

Beyond the SRS: notifications, wishlist, reviews with mentor replies, lesson
notes, learning goals and SkillBot.

</details>

<details>
<summary><b>API overview</b></summary>

Health check: `GET /api/health` returns `{ "ok": true, "users": N, "courses": N }`.

| Area | Endpoints |
|---|---|
| Auth (`/auth`) | `signup`, `verify`, `login`, `forgot`, `forgot-confirm`, `change-password`, `me`, `profile`, `picture` |
| Courses | `/courses`, `/courses/{id}` with nested `lessons`, `quizzes`, `assignments`, `thumbnail`, `resubmit` |
| Learning | `/courses/{id}/learn`, `/lessons/{id}/complete`, `/quizzes/{id}/submit`, `/assignments/{id}/submit`, `/courses/{id}/certificate`, `/my/courses` |
| Payments | `/enroll/free`, `/pay/start`, `/pay/confirm`, `/txns/me`, `/txns/mentor`, `/txns/admin`, `/txns/{id}/receipt` |
| Chat | `/chat/threads`, `/chat/{peer_id}` (history, send, polling with `since_id`, attachments) |
| Match | `/match`, `/meta`, `/skills/resolve`, `/mentors/{id}` |
| Mentor | `/mentor/overview`, `/mentor/profile`, students, quiz results, grading, lesson order, review replies |
| Learner | `/learner/overview`, `/my/certificates`, `/my/results`, `/my/notes`, `/my/goals` |
| Product | `/notifications`, `/wishlist`, `/courses/{id}/reviews` |
| SkillBot | `/bot/ask`, `/bot/starters` |
| Admin (`/admin`) | users, courses, categories, payment methods, reviews, enrollments, refunds, broadcast, export, analytics, mentor verification |

</details>

## Project structure

```
skillhub_prototype/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app, CORS, rate limits
│   │   ├── db.py          # models, PostgreSQL/SQLite engine, demo data
│   │   ├── security.py    # password hashing, JWT
│   │   ├── engine.py      # SkillHub Match scoring
│   │   ├── reports.py     # certificate and receipt PDFs
│   │   └── routers/       # auth, courses, enroll, assess, chat, match,
│   │                      # mentor, learner, product, bot, admin
│   └── tests/             # pytest suite
├── frontend/
│   ├── app/               # Next.js pages: browse, course, learn, match, chat,
│   │                      # dashboard, mentor, profile, login, signup, forgot
│   ├── components/        # LearnerHub, MentorStudio, AdminConsole, Chatbot, ...
│   ├── lib/               # api.js, i18n.js (8 languages)
│   ├── api/               # FastAPI packaged for Vercel
│   └── vercel.json
└── docs/
    ├── MASTER_PRD.md      # full product spec and roadmap
    └── screenshots/
```

## Author

**Durjoy Saha**: design, backend, frontend, tests and deployment.
