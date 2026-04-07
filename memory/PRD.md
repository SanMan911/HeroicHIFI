# Heroic HIFI Foundation - PRD

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB + ReportLab (PDF) + Resend (email) + Emergent Object Storage
- **Auth**: JWT + bcrypt + Email OTP verification + Password Reset
- **Payments**: Razorpay (env-gated)

## Implemented (April 2026)
- [x] 9-page website with logo-matched green-blue gradient theme
- [x] Email OTP verification (Resend) for registration and donations
- [x] Expanded registration: Name, Email, Password, Phone, Age, DOB, Address, PAN, Aadhaar
- [x] 80G Provisional Certificate PDF (50% rebate, auto-generated with donor details)
- [x] PAN mandatory for donations; Aadhaar linked
- [x] Logged-in users get pre-filled donation forms (skip OTP)
- [x] Admin Dashboard: Overview, Donations, Volunteers, Queries, Messages, Tickets, Users tabs
- [x] Admin: status management, 80G certificate download, user deletion
- [x] Activity logging (all site actions to MongoDB)
- [x] Razorpay integration code (order + verify, env-gated)
- [x] English + Hindi bilingual support (full site, all pages, persisted to localStorage)
- [x] Community Directory: volunteers see other members by name/designation/badges/hours
- [x] Community Messaging: send messages to any registered member
- [x] Number stripping: recipients cannot see any digits or number words (EN/HI)
- [x] Admin Messages tab: view all conversation threads unredacted
- [x] **Volunteer Achievement/Badge System**: auto-assigned (Helping Hero all, Century Hero 100+h, Generous Soul 10K+ donated, Community Builder 50+ msgs) + admin-assigned (Star Volunteer Month/Quarter/Year, Top Donor, Rising Star)
- [x] **Profile Page**: DP upload via object storage, volunteer hours, total donated, badges display, edit name/phone/address
- [x] **Admin User Management**: promote/demote, suspend/unsuspend with reason+date, merchandise issued tracking, admin comments, badge assign/remove
- [x] **Grievance Ticket System**: create tickets (subject, description, priority), admin respond/status management
- [x] **Password Reset**: email-based reset flow with secure tokens (30min expiry)
- [x] **Special/Custom Drives**: Birthday celebrations at old-age homes, Memorial/Remembrance donations, Seasonal aid (monsoon umbrellas/raincoats, winter blankets)
- [x] Suspended users blocked from login with reason display

## API Keys Required (Placeholder Mode Active)
1. **Resend API Key** — For email delivery (OTP, password reset emails). Get from: https://resend.com/api-keys
2. **Resend Verified Sender/Domain** — Currently using `onboarding@resend.dev` for testing
3. **Razorpay Key ID + Secret** — For live payment processing. Get from: https://dashboard.razorpay.com/app/keys

## Backlog
### P2: Aadhaar-PAN linking verification via 3rd-party API
### P3: Recurring monthly donation subscriptions
### P4: Go-Live: Replace placeholder Razorpay & Resend keys with live credentials
