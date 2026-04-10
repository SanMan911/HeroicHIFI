# Heroic HIFI Foundation — PRD

## Original Problem Statement
Build a website for "Heroic HIFI Foundation", a Section 8 Non-Profit Organization in India. Features: donations with PAN/80G receipts, OTP-based registration, volunteer onboarding, community messaging (number-stripped), Hindi/English manual translations, volunteer badges, user profiles with avatar upload, Wall of Fame, grievance tickets, password reset via email, and deployment configs for self-hosting.

## Tech Stack
- Frontend: React.js (CRA + Craco + Tailwind + Shadcn/UI)
- Backend: FastAPI + Motor (async MongoDB)
- DB: MongoDB
- Email: Resend (`noreply@heroichifi.org`)
- Payments: Razorpay (placeholder keys)
- Storage: Emergent Object Storage (avatars)
- Deployment: Render (render.yaml), Vercel (vercel.json), Railway (railway.toml)

## Core User Roles
- **Admin** — Full control. Only admins can assign/revoke admin role.
- **Volunteer** — Active participant. Gets badges, merchandise, volunteer-specific emails.
- **Member** — Supporter. Gets subscription updates and donation access.

## Implemented Features (as of Apr 2026)
1. OTP-based registration with role selection (volunteer/member)
2. Login + JWT auth + password reset via email
3. Razorpay donation flow + 80G PDF certificates
4. Community messaging (phone numbers stripped)
5. Volunteer badge/achievement system
6. User profiles with avatar upload
7. Wall of Fame (admin-managed)
8. Grievance ticket system
9. Manual Hindi/English translations
10. WhatsApp floating chat button
11. Special Drives UI (birthdays, memorabilia)
12. **Unified Roster** — single user collection with role-based filtering
13. **Role Change Requests** — users request upgrade/downgrade, admin approves
14. **Drives Management** — CRUD for past & upcoming drives
15. **Activity Logging** — all admin actions logged with timestamps
16. **Age auto-calculation** from DOB
17. Deployment configs: Render (render.yaml), Vercel (vercel.json), Railway

## Deployment Status
- Render: Deployed (both backend + frontend)
- Vercel: Frontend deployed (connected to Render backend)
- Custom domain: heroichifi.org (DNS configured for Vercel)

## Prioritized Backlog
- P1: Refactor server.py (1200+ lines) into modular routes/models
- P2: Aadhaar-PAN linkage verification via 3rd-party API (Sandbox.co.in)
- P3: Recurring monthly donation subscriptions
- P4: Go-Live with real Razorpay keys

## Key API Endpoints
- POST /api/auth/register-init, /api/auth/verify-otp, /api/auth/register
- POST /api/auth/send-reset-link, /api/auth/reset-password
- POST /api/role-requests, GET /api/role-requests/mine
- GET /api/admin/role-requests, PUT /api/admin/role-requests/{id}/approve|reject
- GET /api/drives, POST /api/admin/drives, DELETE /api/admin/drives/{id}
- GET /api/admin/activity-logs
- GET /api/admin/stats (includes role counts, drives, role requests)
- POST /api/donations, GET /api/donations/{id}/certificate

## DB Collections
- users, donations, volunteers, queries, tickets, messages, wall_of_fame, otp_tokens, role_requests, drives, activity_logs
