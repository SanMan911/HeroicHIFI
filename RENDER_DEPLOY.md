# Heroic HIFI Foundation — Render Deployment Guide
# =================================================
#
# COST: $0/month (free tier) or $7/month (always-on backend)
# Frontend is ALWAYS free on Render (static site).
#
# ARCHITECTURE:
#   1. MongoDB Atlas  → Free 512MB cluster (external, not on Render)
#   2. Backend        → Render Web Service (FastAPI)
#   3. Frontend       → Render Static Site (React)
#
# ─────────────────────────────────────────────────
# STEP 1: SET UP MONGODB ATLAS (Free)
# ─────────────────────────────────────────────────
#
#   a. Go to https://cloud.mongodb.com → Sign up / Sign in
#   b. Create a FREE Shared Cluster (M0, 512MB)
#      - Provider: AWS
#      - Region: Mumbai (ap-south-1) for lowest latency
#   c. Database Access → Add user with read/write access
#   d. Network Access → Add 0.0.0.0/0 (allow all IPs)
#   e. Click "Connect" → "Drivers" → Copy the connection string:
#      mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
#
#   Save this — you'll need it as MONGO_URL.
#
# ─────────────────────────────────────────────────
# STEP 2: PUSH CODE TO GITHUB
# ─────────────────────────────────────────────────
#
#   Use "Save to GitHub" in the Emergent chat interface.
#
# ─────────────────────────────────────────────────
# STEP 3: DEPLOY ON RENDER
# ─────────────────────────────────────────────────
#
#   OPTION A — Blueprint (automatic):
#     a. Go to https://render.com → Sign in with GitHub
#     b. Dashboard → "Blueprints" → "New Blueprint Instance"
#     c. Select your GitHub repo
#     d. Render reads render.yaml and creates both services
#     e. Fill in the "sync: false" variables when prompted:
#        - MONGO_URL → paste your Atlas connection string
#        - FRONTEND_URL → (leave blank for now, update after deploy)
#        - REACT_APP_BACKEND_URL → (leave blank for now, update after deploy)
#     f. Click "Apply"
#
#   OPTION B — Manual (if Blueprint doesn't work):
#
#     BACKEND:
#       a. Dashboard → "New" → "Web Service"
#       b. Connect your GitHub repo
#       c. Settings:
#          - Name: heroic-hifi-backend
#          - Region: Singapore
#          - Root Directory: backend
#          - Runtime: Python 3
#          - Build Command: pip install -r requirements.txt
#          - Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
#          - Plan: Free (or Starter $7/mo for always-on)
#       d. Environment Variables: (add all from render.yaml)
#       e. Click "Create Web Service"
#
#     FRONTEND:
#       a. Dashboard → "New" → "Static Site"
#       b. Connect same GitHub repo
#       c. Settings:
#          - Name: heroic-hifi-frontend
#          - Root Directory: frontend
#          - Build Command: yarn install && yarn build
#          - Publish Directory: build
#       d. Environment Variables:
#          - REACT_APP_BACKEND_URL → https://heroic-hifi-backend.onrender.com
#       e. Click "Create Static Site"
#
# ─────────────────────────────────────────────────
# STEP 4: CROSS-LINK URLS (critical!)
# ─────────────────────────────────────────────────
#
#   After both services are deployed, Render assigns URLs like:
#     Backend:  https://heroic-hifi-backend.onrender.com
#     Frontend: https://heroic-hifi-frontend.onrender.com
#
#   a. Go to Backend service → Environment:
#      - Set CORS_ORIGINS → https://heroic-hifi-frontend.onrender.com
#      - Set FRONTEND_URL → https://heroic-hifi-frontend.onrender.com
#      - Save → Render auto-redeploys
#
#   b. Go to Frontend service → Environment:
#      - Set REACT_APP_BACKEND_URL → https://heroic-hifi-backend.onrender.com
#      - Save → Render auto-redeploys
#
# ─────────────────────────────────────────────────
# STEP 5: CUSTOM DOMAIN (optional)
# ─────────────────────────────────────────────────
#
#   a. Frontend service → Settings → Custom Domains → Add heroichifi.org
#   b. Follow Render's DNS instructions (CNAME record)
#   c. Update backend CORS_ORIGINS and FRONTEND_URL to https://heroichifi.org
#
# ─────────────────────────────────────────────────
# STEP 6: VERIFY
# ─────────────────────────────────────────────────
#
#   a. Visit your frontend URL — site should load
#   b. Visit https://heroic-hifi-backend.onrender.com/api/health — should return {"status":"healthy"}
#   c. Try logging in with admin@heroichifi.org / HHF@admin2024
#   d. Test OTP by registering a new user (emails sent via noreply@heroichifi.org)
#
# ─────────────────────────────────────────────────
# TROUBLESHOOTING
# ─────────────────────────────────────────────────
#
#   - "Application error" on backend:
#     Check Render Logs tab → usually a missing env var or dependency
#
#   - CORS errors in browser console:
#     Ensure CORS_ORIGINS matches your EXACT frontend URL (no trailing slash)
#
#   - Frontend shows blank page:
#     Ensure REACT_APP_BACKEND_URL is set correctly and backend is running
#
#   - Cold starts (free tier):
#     First request after 15 min inactivity takes ~30-60 sec. Normal for free plan.
#     Upgrade backend to Starter ($7/mo) for always-on.
#
# =================================================
