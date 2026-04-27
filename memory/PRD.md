# Heroic HIFI Foundation — PRD

## Original Problem Statement
Build a website for "Heroic HIFI Foundation", a Section 8 Non-Profit Organization in India. Features: donations with PAN/80G receipts, OTP-based registration, volunteer onboarding, community messaging (number-stripped), Hindi/English manual translations, volunteer badges, user profiles with avatar upload, Wall of Fame, grievance tickets, password reset via email, and deployment configs.

## Tech Stack
- Frontend: React.js (CRA + Craco + Tailwind + Shadcn/UI)
- Backend: FastAPI + Motor (async MongoDB) — modular routes/, utils/, models/
- DB: MongoDB
- Email: Resend (`noreply@heroichifi.org`) — LIVE
- Payments: Razorpay (test keys active: `rzp_test_ShgRW8UBE4Erlb`)
- Storage: Emergent Object Storage (avatars)
- AI: Gemini 3 Flash via emergentintegrations
- Verification: Sandbox.co.in (PAN/Aadhaar) — placeholder keys, architecture wired
- Deployment: Render (render.yaml), Vercel (vercel.json)

## Backend Architecture
```
backend/
├── server.py (~80 lines — app setup, middleware, startup)
├── config.py
├── routes/
│   ├── auth.py
│   ├── admin.py (large — pending split)
│   ├── donations.py
│   ├── subscriptions.py (NEW — recurring donations)
│   ├── messages.py
│   ├── profile.py
│   ├── general.py
│   └── certificates.py
├── utils/
│   ├── auth.py, email.py, storage.py, privacy.py
│   ├── badges.py, activity.py, llm.py
│   ├── razorpay_subs.py (NEW — Razorpay Subscriptions wrapper)
│   └── sandbox.py (NEW — Sandbox PAN/Aadhaar verification)
├── models/schemas.py
└── data/missions.py
```

## Implemented Features
1. OTP registration with role selection (volunteer/member) + age auto-calc + volunteer specialization (7 areas)
2. Login + JWT + password reset via email
3. Razorpay one-time donations (test keys active) + 80G PDF certificates
4. **Razorpay Subscriptions architecture** (recurring monthly/quarterly) with placeholder plan IDs
5. **Sandbox PAN-Aadhaar verification architecture** with placeholder API keys, admin verify button per user
6. Community messaging (numbers stripped)
7. Volunteer badge system + Star Hero auto-calc (aggregate-based, O(1) DB calls)
8. User profiles with avatar upload
9. Wall of Fame (admin-managed)
10. Grievance ticket system
11. Manual Hindi/English translations
12. Unified Roster + role filter + **specialization filter (7 chips)**
13. Role Change Requests
14. Drives Management (past/upcoming CRUD)
15. Activity Logging (audit trail)
16. Email Blasts (admin → volunteers/members/all)
17. Volunteer Attendance Tracking per drive
18. AI-generated Event Articles (Gemini 3 Flash)
19. Persistent in-app + email notifications
20. Multi-admin approval for admin promotion
21. Mandatory Event Report blocking modal for unreported past drives
22. **Suspend/Unsuspend with mandatory reason (audit-logged with suspended_by/suspended_at)**
23. **Remove user with mandatory reason (≥5 chars) — archived in deleted_users_archive before delete**

## Backlog — Remaining
### P0
- Activate live Razorpay Subscription plans (create plans in Razorpay dashboard, set RAZORPAY_PLAN_MONTHLY / RAZORPAY_PLAN_QUARTERLY in .env)
- Activate Sandbox PAN-Aadhaar verification (user to create sandbox.co.in account, set SANDBOX_API_KEY/SECRET in .env)

### P1
- Swap Razorpay test keys → live keys when ready
- CSV export for roster, donations, activity logs

### P2 — Refactoring (NOT blocking)
- Split routes/admin.py (~620 lines) into per-feature modules (users, events, comms, promotions, misc)
- Split frontend Dashboard.js (~570 lines) into per-tab components in components/dashboard/
- Both files are working with 100% test coverage; splits are stylistic and carry regression risk for no user-visible benefit. Recommend incremental refactor as new features land.

## DB Collections
users, donations, volunteers, queries, tickets, messages, wall_of_fame, otp_tokens, password_reset_tokens, role_requests, drives, activity_logs, notifications, event_reports, email_blasts, admin_promotions, **subscriptions, deleted_users_archive, webhook_events**

## Env Vars (placeholders → live)
- RAZORPAY_PLAN_MONTHLY=plan_PLACEHOLDER_MONTHLY
- RAZORPAY_PLAN_QUARTERLY=plan_PLACEHOLDER_QUARTERLY
- RAZORPAY_WEBHOOK_SECRET=placeholder_webhook_secret_set_in_production
- SANDBOX_API_KEY=placeholder_sandbox_api_key
- SANDBOX_API_SECRET=placeholder_sandbox_api_secret
- SANDBOX_BASE_URL=https://api.sandbox.co.in
