# Heroic HIFI Foundation — PRD

## 🚨 PINNED PRIORITY — REMAINING KEYS PENDING USER ACTION 🚨
**Until these are populated, the corresponding features run in stub/placeholder mode:**

| # | Key | Where to set | What unlocks |
|---|---|---|---|
| 1 | `SANDBOX_API_KEY` | `backend/.env` | PAN verification goes LIVE |
| 2 | `SANDBOX_API_SECRET` | `backend/.env` | PAN-Aadhaar link verification goes LIVE |

**Already activated (✅ LIVE):**
- ✅ `RAZORPAY_KEY_ID` (`rzp_live_SiX7Z60muB4Hpg`) + `RAZORPAY_KEY_SECRET`
- ✅ 4 Razorpay Plans: monthly (₹100), quarterly (₹275), half_yearly (₹525), annual (₹1000)
- ✅ `RAZORPAY_WEBHOOK_SECRET` — auto-charge → donation record + Heroic Patron auto-promotion is live (verified end-to-end with real HMAC signatures)

**Webhook URL configured in Razorpay dashboard:**
`https://hifi-ngo-portal.preview.emergentagent.com/api/subscriptions/webhook`
⚠️ **MUST be updated to the production domain when the app is deployed to a real host (Render/Vercel/custom domain).**

**How to obtain the remaining keys:**
- Sandbox: Sign up at https://sandbox.co.in → Dashboard → API Keys

**This block must remain at the top of every future PRD until all 2 items are LIVE. Action item for next agent: remind the user.**

---

## Original Problem Statement
Build a website for "Heroic HIFI Foundation", a Section 8 Non-Profit Organization in India. Features: donations with PAN/80G receipts, OTP-based registration, volunteer onboarding, community messaging (number-stripped), Hindi/English manual translations, volunteer badges, user profiles with avatar upload, Wall of Fame, grievance tickets, password reset via email, and deployment configs.

## Tech Stack
- Frontend: React.js (CRA + Craco + Tailwind + Shadcn/UI)
- Backend: FastAPI + Motor (async MongoDB) — modular routes/, utils/, models/
- DB: MongoDB
- Email: Resend (`noreply@heroichifi.org`) — LIVE
- Payments: Razorpay **LIVE** (`rzp_live_SiX7Z60muB4Hpg`) — 4 plans active: monthly ₹100, quarterly ₹275, half-yearly ₹525, annual ₹1000
- Storage: Emergent Object Storage (avatars)
- AI: Gemini 3 Flash via emergentintegrations
- Verification: Sandbox.co.in (PAN/Aadhaar) — **keys pending — see PINNED block above**
- Deployment: Render (render.yaml), Vercel (vercel.json)

## Backend Architecture
```
backend/
├── server.py (~80 lines)
├── config.py
├── routes/
│   ├── auth.py, donations.py, subscriptions.py, messages.py
│   ├── profile.py, general.py, certificates.py, admin.py
├── utils/
│   ├── auth.py, email.py, storage.py, privacy.py
│   ├── badges.py, activity.py, llm.py
│   ├── razorpay_subs.py — Razorpay Subscriptions wrapper
│   ├── sandbox.py — Sandbox PAN/Aadhaar verification
│   └── patron.py — Heroic Patron auto-promotion (≥6 charges)
├── models/schemas.py
└── data/missions.py
```

## Implemented Features
1. OTP registration with role selection (volunteer/member) + age auto-calc + volunteer specialization (7 areas)
2. Login + JWT + password reset via email
3. Razorpay one-time donations + 80G PDF certificates
4. Razorpay Subscriptions architecture (recurring monthly/quarterly) — STUB until plan IDs land
5. Sandbox PAN-Aadhaar verification architecture — STUB until API keys land
6. Community messaging (numbers stripped)
7. Volunteer badge system + Star Hero auto-calc (single-aggregate, O(1) DB calls)
8. **Heroic Patron tier** — recurring donors with ≥6 successful charges auto-promoted to dedicated Wall of Fame section + "Heroic Patron" badge
9. User profiles with avatar upload
10. Wall of Fame (admin-managed) with separate Heroic Patrons section above
11. Grievance ticket system
12. Manual Hindi/English translations
13. Unified Roster + role filter + specialization filter (7 chips)
14. Role Change Requests
15. Drives Management (past/upcoming CRUD)
16. Activity Logging (audit trail)
17. Email Blasts (admin → volunteers/members/all)
18. Volunteer Attendance Tracking per drive
19. AI-generated Event Articles (Gemini 3 Flash)
20. Persistent in-app + email notifications
21. Multi-admin approval for admin promotion
22. Mandatory Event Report blocking modal for unreported past drives
23. Suspend/Unsuspend with mandatory reason (audit-logged with suspended_by/at)
24. Remove user with mandatory reason (≥5 chars) — archived in deleted_users_archive before delete
25. **Admin Patrons tab** — list all subscriptions, Recompute button, per-sub Simulate-Charge button (for testing while plan IDs are placeholders)

## Backlog
### P0 — see PINNED block at top
### P1
- Swap Razorpay test → live keys when ready
- CSV export for roster, donations, activity logs

### P2 — Code Org (NOT blocking)
- Split routes/admin.py (~620 lines) into per-feature modules
- Split frontend Dashboard.js (~620 lines) into per-tab components
- Both files have full test coverage; refactor as new features land

## DB Collections
users, donations, volunteers, queries, tickets, messages, wall_of_fame, otp_tokens, password_reset_tokens, role_requests, drives, activity_logs, notifications, event_reports, email_blasts, admin_promotions, subscriptions, deleted_users_archive, webhook_events
