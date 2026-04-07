# Heroic HIFI Foundation - PRD

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB + ReportLab (PDF) + Resend (email)
- **Auth**: JWT + bcrypt + Email OTP verification
- **Payments**: Razorpay (env-gated)

## Implemented (April 2026)
- [x] 9-page website with logo-matched green-blue gradient theme
- [x] Email OTP verification (Resend) for registration and donations
- [x] Expanded registration: Name, Email, Password, Phone, Age, DOB, Address, PAN, Aadhaar
- [x] 80G Provisional Certificate PDF (50% rebate, auto-generated with donor details)
- [x] PAN mandatory for donations; Aadhaar linked
- [x] Logged-in users get pre-filled donation forms (skip OTP)
- [x] Admin Dashboard: Overview, Donations, Volunteers, Queries, Users tabs
- [x] Admin: status management, 80G certificate download, user deletion
- [x] Activity logging (all site actions to MongoDB)
- [x] Razorpay integration code (order + verify, env-gated)
- [x] English + Hindi bilingual support

## Backlog
### P1: Resend + Razorpay API keys to go live
### P2: Aadhaar-PAN linking verification via 3rd-party API
### P3: Recurring monthly donation subscriptions
### P4: Activity log visible in Admin Dashboard
