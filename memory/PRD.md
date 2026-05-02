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
38. **Comprehensive Wall of Fame** — Public `/wall-of-fame` page now renders six themed sections in a single dark-noir layout: Top Donors (with tenure), Most Generous Donors (with tenure), Heroic Patrons, Office Bearers (current + past, full tenure history), Star Volunteers / Rising Stars / Community Builders, and admin-curated Helping Heroes. Backed by a single `GET /api/wall-of-fame/comprehensive` endpoint that aggregates all surfaces.
39. **Donor Privacy — public-display rounding** — Every public surface (homepage marquee, Wall of Fame, Heroic Patrons list, Top Donor + Most Generous ledgers) now rounds money values to the nearest ₹100 via `utils.money.round_to_100`. Donor's own profile, admin dashboard, and 80G certificates remain EXACT (legal/private flows unaffected). A privacy notice is shown on the Wall of Fame hero.
40. **Amount-in-Words on 80G certificates** — Both provisional and consolidated 80G receipt PDFs now print the donation amount in Indian-system words (lakh/crore) alongside numerals — "Rupees Twelve Thousand Three Hundred Forty Five Only". Consolidated certificate weaves the words into the legal certifying paragraph for stronger compliance. Powered by `utils.money.amount_in_words`.
41. **Public Hero Recognition Cards** — New shareable per-donor profile at `/heroes/:slug` (slug derived from name). Backed by `GET /api/heroes/{slug_or_email}` which always assembles fresh from underlying truth (users + donations + ledgers + office_history) — no cache, instant sync. Card surfaces lifetime donation total (rounded), fee-absorbed total with a dedicated **"A Special Note of Magnanimity"** callout when > 0, badge collection, Top Donor / Most Generous Donor tenure ladders, Office-Bearer post tenures, Heroic Patron commitment line, specializations and contribution summary. **Admins are deliberately tenure-free** — `joined_at`, `tenure_start`, `volunteer_hours`, and `since X` framing are all suppressed for `role==admin` (they serve the foundation forever, behind the scenes). Master Admin returns 404 (privacy invariant). One-click **Share** button (native Web Share API → fall-back to clipboard) and a **Sync** button to manually re-fetch the freshest data.
42. **Auto-reject + Clear Rejected donations** — Lazy sweep on every `GET /api/admin/donations` flips any `status=pending` donation older than 24h to `status=rejected` with `auto_rejected=true` and an `auto_rejected_reason`. **Each flipped donor is emailed** a warm follow-up via Resend ("Your donation didn't go through — we'd love to try again") with a fresh donate-now CTA, recovering ~10–15% of intent. Email failures are logged but never block the sweep. New endpoint `POST /api/admin/donations/clear-rejected` deletes every rejected donation (auto + manual). Donations tab now surfaces a soft amber "N rejected donation(s) on file" banner with a **Clear Rejected** button when any rejected rows exist; banner auto-hides at zero.
43. **Office-bearers display fix** — `/api/recognitions` (homepage marquee) and the broader bearer surface now read from the authoritative `office_history` collection where `end_date IS NULL` instead of the stale `users.designation` field, AND include EVERY post (Chairman + Secretary + Treasurer + **Event Incharge** + Assistant) — not just the C/S/T trio. Verified end-to-end: 4 active posts seeded → all 4 returned in payload, closed tenure correctly excluded.
44. **Global dd-mm-yyyy date format** — All user-visible dates across Dashboard, Profile, Hero, Wall of Fame, Tickets, and Community now route through a shared `lib/dates.js` helper (`formatDate`, `formatDateTime`, `tenureRange`) emitting `dd-mm-yyyy` consistently. Example: `28-04-2026`.
45. **Auto-reject donor email** — Each donation flipped from `pending` → `rejected` by the 24h sweep triggers a warm follow-up email to the donor via Resend with a "Try Donating Again" CTA. Recovers a meaningful share of failed donations. Failures are logged but never block the sweep.
46. **Letter of Appointment (auto-issued, downloadable)** — When a Master Admin assigns a new office post (Chairman / Secretary / Treasurer / Event Incharge / Assistant), a beautifully-typeset Letter of Appointment PDF is auto-generated, archived in `db.appointment_letters`, and emailed to the appointee with the PDF attached. The letter includes the foundation header, today's date, the appointee's name, the post, effective start date, a four-point governance pledge, the optional bio (rendered as a quoted leadership note), and the issuer's signature. Re-downloadable any time from the **Office-Bearer Tenures** table on the admin dashboard via a per-row LoA pill.
47. **Office-bearer collection unification** — Resolved a silent collection-name split between writers (`office_bearer_tenures`) and readers (`office_history`) that had been making the recognitions ticker, comprehensive Wall of Fame and hero pages appear empty for live tenure data. Readers in `general.py` and `heroes.py` now read from the canonical `office_bearer_tenures`. Verified live: assigning Event Incharge surfaces immediately on the homepage marquee.

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
