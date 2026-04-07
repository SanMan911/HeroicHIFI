# Heroic HIFI Foundation — Vercel Deployment Guide
# =================================================
#
# WHY VERCEL?
#   - Always free for frontend (no cold starts, unlike Render)
#   - Global CDN (faster load times across India)
#   - Automatic HTTPS & preview deployments on every push
#   - Backend stays on Render (Vercel doesn't support Python)
#
# COST: $0/month (Hobby plan — free forever for personal projects)
#
# ARCHITECTURE:
#   Backend  → Render Web Service (already deployed)
#   Frontend → Vercel Static Site (this guide)
#
# ─────────────────────────────────────────────────
# STEP 1: SIGN UP ON VERCEL
# ─────────────────────────────────────────────────
#
#   a. Go to https://vercel.com → Sign up with GitHub
#   b. Authorize Vercel to access your repositories
#
# ─────────────────────────────────────────────────
# STEP 2: IMPORT YOUR PROJECT
# ─────────────────────────────────────────────────
#
#   a. Click "Add New..." → "Project"
#   b. Find and select your "HeroicHIFI" repo
#   c. Configure the project:
#      - Framework Preset: Other
#      - Root Directory: Click "Edit" → type "frontend" → confirm
#      - Build Command: npm install --legacy-peer-deps && CI=false npm run build
#      - Output Directory: build
#      - Install Command: npm install --legacy-peer-deps
#
# ─────────────────────────────────────────────────
# STEP 3: SET ENVIRONMENT VARIABLE
# ─────────────────────────────────────────────────
#
#   Before clicking "Deploy", expand "Environment Variables" and add:
#
#     KEY:   REACT_APP_BACKEND_URL
#     VALUE: https://heroic-hifi-backend.onrender.com
#
#   (Use your actual Render backend URL)
#
# ─────────────────────────────────────────────────
# STEP 4: DEPLOY
# ─────────────────────────────────────────────────
#
#   a. Click "Deploy"
#   b. Wait 1-2 minutes for the build
#   c. Vercel assigns a URL like: https://heroic-hifi.vercel.app
#
# ─────────────────────────────────────────────────
# STEP 5: UPDATE BACKEND CORS (critical!)
# ─────────────────────────────────────────────────
#
#   Go to Render → heroic-hifi-backend → Environment:
#
#   Update CORS_ORIGINS to include your Vercel URL:
#     https://heroic-hifi.vercel.app
#
#   Update FRONTEND_URL:
#     https://heroic-hifi.vercel.app
#
#   Save → backend auto-redeploys.
#
#   NOTE: If you want BOTH Render frontend and Vercel frontend
#   to work, set CORS_ORIGINS to:
#     https://heroic-hifi-frontend.onrender.com,https://heroic-hifi.vercel.app
#
# ─────────────────────────────────────────────────
# STEP 6: CUSTOM DOMAIN (optional)
# ─────────────────────────────────────────────────
#
#   a. Vercel Dashboard → your project → Settings → Domains
#   b. Add: heroichifi.org
#   c. Vercel shows DNS instructions:
#      - Add an A record: 76.76.21.21
#      - Or CNAME: cname.vercel-dns.com
#   d. Update Render backend CORS_ORIGINS and FRONTEND_URL
#      to https://heroichifi.org
#
# ─────────────────────────────────────────────────
# STEP 7: VERIFY
# ─────────────────────────────────────────────────
#
#   a. Visit your Vercel URL — site should load instantly
#   b. Login with admin@heroichifi.org / HHF@admin2024
#   c. Test donations, messaging, profile upload
#
# ─────────────────────────────────────────────────
# VERCEL vs RENDER FRONTEND — COMPARISON
# ─────────────────────────────────────────────────
#
#   Feature          | Render Static  | Vercel
#   -----------------+----------------+-----------
#   Cost             | Free           | Free
#   Cold starts      | None (static)  | None
#   CDN              | Global         | Global (faster edge network)
#   Preview deploys  | No             | Yes (every PR gets a preview URL)
#   Custom domain    | Yes            | Yes (easier setup)
#   Auto-deploy      | Yes (on push)  | Yes (on push)
#   Build speed      | ~2-3 min       | ~1-2 min
#
#   VERDICT: Vercel is slightly better for frontend hosting.
#   You can use Vercel for frontend + Render for backend.
#
# ─────────────────────────────────────────────────
# TROUBLESHOOTING
# ─────────────────────────────────────────────────
#
#   - Build fails: Check Vercel build logs (Deployments tab)
#   - CORS errors: Ensure backend CORS_ORIGINS matches your exact Vercel URL
#   - API not connecting: Verify REACT_APP_BACKEND_URL is set correctly
#   - 404 on page refresh: The vercel.json rewrites handle SPA routing
#
# =================================================
