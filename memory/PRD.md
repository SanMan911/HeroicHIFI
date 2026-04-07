# Heroic HIFI Foundation - PRD

## Original Problem Statement
Build a beautiful website for "Heroic HIFI Foundation", a Section 8 Company in India (CIN: U88900BR2024NPL072593). Features include 7 charitable missions, donation acceptance, volunteer registration, mission-specific queries, login functionality, English+Hindi language support, and SEO optimization.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Auth**: JWT token-based (localStorage), bcrypt password hashing
- **Design**: Cormorant Garamond + Outfit fonts, warm sand/blue/orange palette

## User Personas
- **Donors**: Individuals wanting to contribute financially
- **Volunteers**: People wanting to donate time/skills
- **Visitors**: General public learning about the foundation
- **Admin**: Foundation staff managing the platform

## Core Requirements (Static)
1. Multi-page website (Home, About, Missions, Donate, Volunteer, Contact, Login, Dashboard)
2. 7 Missions showcase with detail pages
3. Donation form with preset amounts and PAN/80G support
4. Volunteer registration with interest selection
5. Contact/Query form with mission-specific dropdown
6. JWT authentication system
7. English + Hindi bilingual support
8. SEO meta tags and Open Graph support
9. Razorpay payment gateway (pending integration)

## What's Been Implemented (April 2026)
- [x] Full website with 9 pages and responsive design
- [x] Backend API with auth, missions, donations, volunteers, queries endpoints
- [x] Admin seeding (admin@heroichifi.org)
- [x] Language toggle (EN/HI) with hand-written Hindi translations
- [x] Glass morphism header with logo
- [x] Hero section with overlay, marquee, bento grid missions
- [x] Blood donation drives and Community Kitchen (Langar) sections
- [x] SEO meta tags (title, description, OG, Twitter cards)
- [x] All forms functional and connected to backend APIs

## Prioritized Backlog
### P0 (Critical)
- Razorpay payment gateway integration (requires API keys from user)
- Admin dashboard with donation/volunteer/query management

### P1 (High)
- Email notifications for new donations/volunteers/queries
- 80G tax receipt generation
- Photo gallery for past events

### P2 (Nice to have)
- Blog/News section
- Event calendar
- Volunteer testimonials
- Social media integrations
