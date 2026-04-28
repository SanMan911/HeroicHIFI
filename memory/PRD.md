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
- ✅ `RAZORPAY_WEBHOOK_SECRET` — auto-charge → donation record + Heroic Patron auto-promotion + 80G PDF auto-emailed (verified end-to-end)
- ✅ Production webhook URL set in Razorpay dashboard: `https://heroic-hifi-backend.onrender.com/api/subscriptions/webhook`

**How to obtain the remaining keys:**
- Sandbox: Sign up at https://sandbox.co.in → Dashboard → API Keys

**This block must remain at the top of every future PRD until all 2 items are LIVE. Action item for next agent: remind the user.**

---

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
25. Admin Patrons tab — list all subscriptions, Recompute, per-sub Simulate-Charge
26. **Provisional vs Consolidated 80G separation** — per-donation emails are clearly marked PROVISIONAL (no legal weight); legal **consolidated 80G** is emailed once a year on 1 April for the prior FY
27. **Webhook Health widget** — pass-rate chip, event log, replay button per row
28. **Two-admin gate on Annual 80G dispatch** — separation-of-duties: drafter cannot self-approve (unless Master Admin). Admin A drafts → Admin B approves & dispatches. Daemon also creates a draft (never auto-sends).
29. **Master Admin tier** — `admin@heroichifi.org` is HIDDEN from other admins (roster, activity logs, stats, all per-user endpoints return 404) and has master override on: Annual 80G self-approve, one-step admin promotion (skips multi-admin gate). Master override actions log `override=true` for audit trail. Master Admin badge shown only to super-admin in the dashboard header.
30. **Office-Bearer Posts** — Chairman, Secretary, Treasurer (all unique), Event Incharge & Assistant (multi-holder). Editable inline from each Roster card by Master Admin. Tenure history (start/end/reason) is preserved in `office_history` and exported in the AGM Report PDF.
31. **Specialization Lifetime Limit** — New volunteer registrants must select **at least 3** specializations to enable the *Verify & Register* button. After registration, each volunteer can edit their specializations a maximum of **2 times in their lifetime** via Profile → My Specializations. Counter (`specialization_edits_remaining`, default 2) is decremented atomically; volunteers see "X edits remaining" and are blocked at 0.
32. **Webhook Health Reset** — Master Admin only "↻ Reset history" button on the Razorpay Webhook Health widget purges historical webhook events (useful after rotating the secret or migrating from preview→production). Smarter dual-banner: hard error when zero verified, soft amber notice when historical noise skews the pass-rate.
33. **Cover-Fee donor warm-copy** — Provisional-receipt email now embeds a green-banner thank-you paragraph when `fee_covered > 0`, explicitly clarifying that only the pledged base (₹X) qualifies for 80G — the absorbed Razorpay fee (₹Y) is a payment to Razorpay, not a tax-deductible donation.
34. **My Donations on Profile** — Logged-in donor sees their full donation history at `/profile`, with a small heart badge ("fee covered") + breakdown line `Pledged ₹X · +₹Y fees · Total ₹Z` whenever `fee_covered > 0`. Confirmed donations expose a one-click Receipt download. Backed by `GET /api/donations/mine` (auto-defaults legacy rows).
35. **Admin CSV Exports** — Overview tab now offers one-click CSV downloads for Roster, Donations (incl. fee_covered/gross_amount), and Activity Logs (last 90 days). Master Admin's row and actions are hidden from non-master admins to preserve the hidden-master invariant. Endpoints: `GET /api/admin/export/{roster,donations,activity}.csv`.
36. **Lifetime Cover-Fee Banner** — Profile → My Donations now shows a warm rose-pink banner totalling all fees the donor has voluntarily absorbed: "You've absorbed ₹X in processing fees so far 💚 — the foundation received every rupee of your ₹Y pledge." Banner only appears when `total_fee_covered > 0`.
37. **"Most Generous Donor" Award** — Standalone real-time engine (`utils/most_generous.py`) ranks donors by total fee_covered in the current FY. Successor must STRICTLY exceed the incumbent (same rule as Top Donor). Materialises the rose "Most Generous Donor" badge atomically — pulled from previous holder, added to the new leader. Surfaces in homepage Recognitions ticker, Wall of Fame, admin badge dropdown. Ledger preserved in `db.most_generous_ledger`. Public endpoint: `GET /api/most-generous-ledger`. Hooked into the same recompute pipeline as Top Donor (verify-payment, subscription webhook, simulate-charge, replay).

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
