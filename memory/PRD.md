# Heroic HIFI Foundation - PRD

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB + ReportLab (PDF) + Resend (email, LIVE) + Emergent Object Storage
- **Auth**: JWT + bcrypt + Email OTP verification + Password Reset
- **Payments**: Razorpay (env-gated, placeholder keys)

## Implemented (April 2026)
- [x] 10+ page website with logo-matched green-blue gradient theme
- [x] Email OTP verification (Resend, LIVE via noreply@heroichifi.org)
- [x] Expanded registration: Name, Email, Password, Phone, Age, DOB, Address, PAN, Aadhaar
- [x] 80G Provisional Certificate PDF (50% rebate, auto-generated)
- [x] PAN mandatory for donations; Aadhaar linked
- [x] Logged-in users get pre-filled donation forms (skip OTP)
- [x] Admin Dashboard: Overview, Donations, Volunteers, Queries, Messages, Tickets, Users (7 tabs)
- [x] Admin: status management, 80G certificate download, user deletion
- [x] Activity logging (all site actions to MongoDB)
- [x] Razorpay integration code (order + verify, env-gated)
- [x] English + Hindi bilingual (all pages, persisted to localStorage)
- [x] Community Directory + Messaging with number stripping (EN/HI)
- [x] Admin Messages tab: unredacted thread viewing
- [x] Badge System: auto (Helping Hero, Century Hero, Generous Soul, Community Builder) + admin (Star Volunteer Month/Quarter/Year, Top Donor, Rising Star)
- [x] Profile Page: DP upload, hours, total donated, badges, edit profile
- [x] Admin User Management: promote/demote, suspend/unsuspend, merchandise tracking, comments, badge assign/remove
- [x] Grievance Ticket System: create/view/respond/manage status
- [x] Password Reset: email-based with secure tokens (30min expiry)
- [x] Special/Custom Drives: Birthday at old-age homes, Memorial donations, Seasonal aid
- [x] **Wall of Fame**: beautiful dark-themed public page honouring distinguished members, admin toggle from Dashboard
- [x] Resend API LIVE with verified domain heroichifi.org

## API Keys Status
- **Resend**: LIVE (re_C4DoEz3H_..., sender: noreply@heroichifi.org)
- **Razorpay**: Placeholder (awaiting live keys)

## Backlog
### P2: Aadhaar-PAN linking verification via 3rd-party API
### P3: Recurring monthly donation subscriptions
### P4: Go-Live: Replace placeholder Razorpay keys with live credentials
