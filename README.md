# Skillhub - One Platform to Learn Every Skill

Full-stack implementation of the Skillhub platform from the AIUB SE project SRS
(77-page spec, 24 functional requirements) plus the SkillHub Match mentor-matching
engine - built with FastAPI + SQLite + Next.js, no heavyweight dependencies.

## Run
```
run-backend.cmd     # venv + uvicorn on http://localhost:8030
run-frontend.cmd    # next dev on http://localhost:3030
```## Demo accounts
| Role    | Email                  | Password    |
|---------|------------------------|-------------|
| Admin   | admin@skillhub.dev     | Admin123    |
| Mentor  | rifat@skillhub.dev     | Mentor123   |
| Learner | learner@skillhub.dev   | Learner123  |

## SRS requirement coverage (all 24)
1. Signup with name/email/BD 11-digit phone/role + strong password rules
2. Email OTP verification activates the account (dev_otp returned)
3. Login with lockout after 5 failed attempts (30 min) - status: unverified/active/blocked
4. Forgot password via OTP + change password from profile
5. Profile view/edit (name, phone, DOB, country, bio, language)
6. Course creation by mentors -> admin approval -> published
7. Lessons with file upload (served from /files/)
8. Enrollment: free instant, paid via simulated bank (card 12-19 digits, PIN, bank OTP)
9. Quizzes: timed, passing score, max attempts, per-question review
10. Assignments: file submission + drafts, mentor can view submissions
11. Progress tracking (70% lessons / 30% quizzes) + certificate PDF on completion
12. 1:1 chat learner and mentor with attachments (polling)
13. Multi-language UI EN/BN toggle persisted per user (PUT /auth/profile)
14. Search + filters (keyword, category, language, max price, min rating)
15. SkillHub Match: ranked mentor list with match percent, breakdown, reasons
16. Admin course approval queue (publish/reject)
17. Admin transaction log (status/date filters, revenue total)
18. Mentor transaction view + total earned
19. Learner transaction history + PDF receipts (SH-YYYYMMDD-XXXX refs)
20. User management: block, unblock, permanent removal (admins protected)
21. Payment method management (add, enable/disable - UCB/BRAC/City/bKash seeded)
22. Admin analytics: users by role, courses by status, enrollments, revenue, top courses
23. Role dashboards: learner / mentor / admin (/dashboard)
24. Platform landing + browse for guests (published courses only)
## API map
- /auth/* : signup, verify, login, forgot, forgot-confirm, change-password, me, profile
- /courses, /courses/id, /courses/id/lessons, /courses/id/learn, /courses/id/certificate
- /quizzes/id, /quizzes/id/submit, /assignments/id/submit, /assignments/id/submissions, /lessons/id/complete, /my/courses
- /enroll/free, /pay/start, /pay/confirm, /txns/me, /txns/mentor, /txns/admin, /txns/id/receipt
- /chat/threads, /chat/peer (GET with since_id polling, POST text/file)
- /admin/users, /admin/courses, /admin/payment-methods, /admin/analytics, /admin/users/id/status
- /match, /meta, /skills/resolve, /mentors/id - matching engine (app/engine.py, ported from skillhub-match)
- /files/name uploads, /api/health

## Tests
```
cd backend
.venv\Scripts\python -m pytest tests -q     (17 passed)
```

## Structure
```
backend/app/    security.py  db.py  deps.py  engine.py  reports.py  routers/(auth, courses, enroll, assess, chat, admin, match).py
backend/tests/  test_api.py (10) + test_engine.py (7)
frontend/app/   pages: landing, login, signup, forgot, browse, course detail, learn, match, chat, profile, dashboard
frontend/lib/   api.js, i18n.js (EN/BN dictionaries)
frontend/components/Nav.jsx  role-aware nav + language toggle
```

## Notes
- Passwords/hashes never leave the backend; JWT carries only id + role (12 h expiry).
- Payment + OTP are simulations - no real money, no real email (per SRS dev constraints).
- Blocked users get 403 at every authenticated endpoint.
