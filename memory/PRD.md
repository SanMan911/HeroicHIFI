# Heroic HIFI Foundation - PRD

## Original Problem Statement
Build a website for "Heroic HIFI Foundation", a Section 8 Company in India (CIN: U88900BR2024NPL072593). Features include 7 charitable missions, donation acceptance via Razorpay, volunteer registration, mission-specific queries, admin login + dashboard, English+Hindi language, SEO optimization.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Auth**: JWT token-based, bcrypt password hashing
- **Payments**: Razorpay integration (env-gated)
- **Design**: Cormorant Garamond + Outfit fonts, logo-matched palette (green-blue gradient, navy, sky blue, amber orange)

## What's Been Implemented (April 2026)
- [x] 9-page website (Home, About, Missions, MissionDetail, Donate, Volunteer, Contact, Login, Dashboard)
- [x] Full Admin Dashboard with Overview stats, Donations/Volunteers/Queries management tabs, status updates
- [x] Razorpay integration code (order creation, checkout.js, payment verification) — needs API keys
- [x] JWT auth with admin role-based access control
- [x] 403 protection on admin endpoints for non-admin users
- [x] English + Hindi bilingual support with hand-written translations
- [x] Logo-matched color theme across all pages
- [x] SEO meta tags

## Prioritized Backlog
### P1
- Add Razorpay API keys to activate live payments
- Email notifications for new donations/volunteers/queries
- 80G tax receipt generation

### P2
- Blog/News section
- Photo gallery for past events
- Event calendar
- Volunteer testimonials
