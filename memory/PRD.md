# Heroic HIFI Foundation — PRD

## Original Problem Statement
Build a website for "Heroic HIFI Foundation", a Section 8 Non-Profit Organization in India. Features: donations with PAN/80G receipts, OTP-based registration, volunteer onboarding, community messaging (number-stripped), Hindi/English manual translations, volunteer badges, user profiles with avatar upload, Wall of Fame, grievance tickets, password reset via email, and deployment configs.

## Tech Stack
- Frontend: React.js (CRA + Craco + Tailwind + Shadcn/UI)
- Backend: FastAPI + Motor (async MongoDB) — **MODULAR** (routes/, utils/, models/)
- DB: MongoDB
- Email: Resend (`noreply@heroichifi.org`)
- Payments: Razorpay (test keys active: `rzp_test_ShgRW8UBE4Erlb`)
- Storage: Emergent Object Storage (avatars)
- Deployment: Render (render.yaml), Vercel (vercel.json)

## Backend Architecture (Post-Refactor)
```
backend/
├── server.py (80 lines — app setup, middleware, startup)
├── config.py (DB connection, constants)
├── routes/
│   ├── auth.py (register, login, OTP, password reset)
│   ├── admin.py (user mgmt, stats, tickets, drives, wall of fame)
│   ├── donations.py (Razorpay flow, certificates)
│   ├── messages.py (community messaging, privacy)
│   ├── profile.py (user profile, avatar upload)
│   ├── general.py (volunteers, queries, missions, drives, wall of fame public)
│   └── certificates.py (80G PDF generation)
├── utils/
│   ├── auth.py (JWT, password, dependencies)
│   ├── email.py (OTP, reset, registration notification)
│   ├── storage.py (Emergent Object Storage)
│   ├── privacy.py (number stripping)
│   ├── badges.py (auto-badge computation)
│   └── activity.py (audit logging)
├── models/schemas.py (all Pydantic models)
└── data/missions.py (mission data)
```

## Core User Roles
- **Admin** — Full control. Only admins can assign/revoke admin role.
- **Volunteer** — Active participant. Gets badges, merchandise, volunteer-specific emails.
- **Member** — Supporter. Gets subscription updates and donation access.

## Implemented Features
1. OTP registration with role selection (volunteer/member) + age auto-calc from DOB + volunteer specialization multi-select (7 areas)
2. Login + JWT + password reset via email
3. Razorpay donations (test keys active) + 80G PDF certificates
4. Community messaging (phone numbers stripped)
5. Volunteer badge/achievement system
6. User profiles with avatar upload
7. Wall of Fame (admin-managed)
8. Grievance ticket system
9. Manual Hindi/English translations
10. Unified Roster with role-based filtering
11. Role Change Requests (user → admin approval)
12. Drives Management (past/upcoming CRUD)
13. Activity Logging (audit trail)
14. Registration notification to heroic.hifi@proton.me
15. PAN verified/unverified tracking in admin stats
16. Deployment: Render + Vercel (both live)

## Prioritized Backlog
### P0 - Next Sprint (User Requested)
- Recurring monthly donations (Razorpay Subscriptions)
- PAN-Aadhaar verification via Sandbox API (waiting on user account)

### Phase 2 - DONE (2026-04-27)
- Email blasts (admin → volunteers/members/all) ✅
- Volunteer attendance tracking per drive ✅
- AI-generated event articles via Gemini 3 Flash ✅
- In-app + email notifications (persistent) ✅
- Star Hero scoring (attendance + hours + rating) ✅
- Registration volunteer specialization (7 categories) ✅
- Multi-admin approval for admin promotion ✅
- Mandatory blocking modal for unreported past drives ✅

### P1 - Later
- PAN-Aadhaar verification via Sandbox API
- Swap Razorpay to live keys
- CSV data export

## DB Collections
users, donations, volunteers, queries, tickets, messages, wall_of_fame, otp_tokens, password_reset_tokens, role_requests, drives, activity_logs
