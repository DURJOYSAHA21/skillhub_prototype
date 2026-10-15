# SkillHub - MASTER Product Spec (the full version)

> This is the complete, brainstormed feature universe for SkillHub. It supersedes
> the narrow "Product Hardening" plan fragment. Built from: the 77-page AIUB SE
> SRS (24 functional requirements) + what "the world would actually use"
> (Coursera / Udemy / Duolingo-class platform). Audited against the real code.
>
> Status legend: [DONE] built & verified | [PARTIAL] exists, needs work | [TODO] not built

## Vision
One global, multi-language learning platform: anyone, in any language, can
discover trusted courses, learn them end-to-end, get certified, pay/get-paid,
and belong to a community. University SRS is the floor; this doc is the ceiling.

---
## Epic 0 - Core SRS (24 requirements) - the floor
[DONE] Signup+OTP+BD-phone, login+lockout, forgot/change pw, profile, course
  create->admin-approve->publish, lessons+file upload, enroll (free + simulated
  bank), quizzes (timed/scoring/attempts), assignments+submissions, progress+
  certificate PDF, 1:1 chat+attachments, EN/BN UI persisted, search+filters,
  SkillHub Match ranked mentors, admin approval queue, txn log (admin/mentor/
  learner + receipts), user block/unblock/remove, payment-method mgmt, admin
  analytics, role dashboards, guest landing+browse.

## Epic 1 - Language & Accessibility (the product's soul)
[DONE] 8-language UI dictionaries (en/bn/hi/ar/es/fr/zh/id), RTL (Arabic),
  language persisted per account, hydration on login.
[PARTIAL] Dictionary coverage: deep marketing/auth copy falls back to English
  for es/fr/ar/zh/id; sort options & some placeholders untranslated.
[TODO] All 14 SRS course-languages selectable in UI switcher; per-lesson audio/
  captions language tags; full RTL polish for forms/modals; WCAG AA contrast +
  screen-reader labels + keyboard nav; auto-detect browser language on first visit.

## Epic 2 - Discovery & Trust (strangers -> users)
[DONE] Public browse, filters (category/language/level/price/rating), sort,
  wishlist heart, instructor links to public mentor page, "New - not rated".
[PARTIAL] Ratings shown as single number.
[TODO] Ratings DISTRIBUTION (5->1 star histogram + review count); home "Browse
  by category" rail (icon tiles); course PREVIEW/trailer + curriculum outline on
  card; VERIFIED instructor badge + years/students count; popularity ("12,480
  enrolled"); trending / bestseller tags; personalized "Recommended for you";
  SEO meta + sitemap + JSON-LD Course schema; share links.

## Epic 3 - Learning Experience
[DONE] Lesson viewer with notes + video embed, quiz taking + per-question review,
  assignment submit + drafts, progress (70/30), certificate.
[PARTIAL] Certificate verification link.
[TODO] Learning PATHS (curated multi-course sequences w/ next-up); lesson
  bookmarks + personal notes + notes export; in-course Q&A/discussion threads;
  resume-last-lesson; download resources; mobile note pad; captioned video.

## Epic 4 - Engagement & Retention (keep the world coming back)
[TODO] Daily streaks + XP + levels + badges; course reminders via notifications;
  progress nudge emails/in-app; "continue where you left off" rail; learner goals
  (minutes/week) + time tracking; leaderboards (opt-in); certificates wall.

## Epic 5 - Mentor / Creator Tools
[DONE] Course/lesson/quiz/assignment builders, mentor txn view + total earned,
  view submissions, chat.
[TODO] Instructor analytics (enrollees, completion rate, revenue by course,
  ratings trend); course drafts + preview-before-publish; bulk lesson import;
  coupon creation by mentor; announcements to enrolled learners; payout method
  + payout schedule (currently only "total earned", no withdrawal).

## Epic 6 - Marketplace & Monetization
[DONE] Simulated bank (UCB/BRAC/City/bKash), free+paid enroll, receipts, txn logs.
[TODO] Multi-CURRENCY (BDT default + USD/INR/EUR with rates); coupons/discounts +
  sales; course bundles; refunds; instructor payout/withdrawal + platform fee
  split; tax/invoice PDF; real gateway abstraction (Stripe/bKash) behind a flag.

## Epic 7 - Community & Social
[DONE] 1:1 learner<->mentor chat with attachments + polling.
[TODO] Course discussion forums + upvotes; cohort / live-class scheduling;
  peer study groups; follow mentors; review "helpful" votes; mentor announcements;
  user reports + moderator queue.

## Epic 8 - Trust, Safety & Admin
[DONE] RBAC, JWT (id+role), blocked-user 403, admin approval/analytics/users.
[TODO] Content moderation queue (report course/review/user); plagiarism/
  profanity checks; admin bulk actions + audit log; GDPR export/delete my data;
  rate limiting; secure headers; sensitive-action re-auth.

## Epic 9 - Platform / Technical
[DONE] FastAPI+SQLite+Next.js, pytest suite, prod build, notifications bell.
[PARTIAL] PWA/offline, caching.
[TODO] PWA (installable, offline shell); image/CDN + WebP; lighthouse perf >90;
  DB backup/restore (SRS NFR daily backups); error tracking (Sentry); analytics
  (privacy-first); feature flags; CI (lint+test+build); staging/preview deploys.

---
## BUILD QUEUE (priority order for "make the world use it")
1. Discovery & trust pass  (home category rail, ratings distribution, verified
   badge, enrollment counts, preview/curriculum on card, mobile-first polish)
2. Language coverage finish (all UI strings in all 8 langs, sort/labels localized,
   browser-lang auto-detect)
3. Learning paths + bookmarks + notes + in-course Q&A
4. Streaks / XP / badges / continue-learning rail
5. Multi-currency + coupons + instructor payouts
6. Community (course discussion, cohorts, announcements) + reporting/moderation
7. PWA + SEO + performance + backups + deploy