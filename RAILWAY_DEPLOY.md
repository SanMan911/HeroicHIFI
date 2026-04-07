# Heroic HIFI Foundation — Railway Deployment Guide
# ================================================
#
# ARCHITECTURE (3 Railway services):
#   1. MongoDB   → Railway Database plugin (free with Hobby)
#   2. Backend   → FastAPI (from /backend)
#   3. Frontend  → React static build (from /frontend)
#
# STEP-BY-STEP:
#
# 1. Push this repo to GitHub using "Save to GitHub" in Emergent
#
# 2. Go to https://railway.app → Sign in with GitHub
#
# 3. Create New Project → "Deploy from GitHub Repo" → Select your repo
#
# 4. ADD MONGODB:
#    - Click "+ New" → "Database" → "MongoDB"
#    - Railway auto-generates MONGO_URL (find it under Variables tab)
#
# 5. ADD BACKEND SERVICE:
#    - Click "+ New" → "GitHub Repo" → Select same repo
#    - Settings tab:
#        Root Directory: /backend
#        Builder: Dockerfile
#    - Variables tab (add all):
#        MONGO_URL           → ${{MongoDB.MONGO_URL}}  (use Railway variable reference)
#        DB_NAME             → heroic_hifi
#        JWT_SECRET          → a7f3b2c9d4e5f6a1b8c3d0e7f2a9b4c5d6e1f8a3b0c7d2e9f4a5b6c1d8e3f0
#        RESEND_API_KEY      → re_C4DoEz3H_9MfR5CB4zp9mFGSYHdfRX4Ki
#        SENDER_EMAIL        → noreply@heroichifi.org
#        EMERGENT_LLM_KEY    → sk-emergent-92e7e3bE9E6C161Ef7
#        ADMIN_EMAIL         → admin@heroichifi.org
#        ADMIN_PASSWORD      → HHF@admin2024
#        CORS_ORIGINS        → https://<your-frontend>.up.railway.app
#        FRONTEND_URL        → https://<your-frontend>.up.railway.app
#        PORT                → 8001
#    - Networking tab:
#        Generate a public domain (e.g., backend-xxx.up.railway.app)
#
# 6. ADD FRONTEND SERVICE:
#    - Click "+ New" → "GitHub Repo" → Select same repo
#    - Settings tab:
#        Root Directory: /frontend
#        Builder: Dockerfile
#    - Variables tab:
#        REACT_APP_BACKEND_URL → https://<your-backend>.up.railway.app
#        PORT                  → 3000
#    - Networking tab:
#        Generate a public domain OR link your custom domain
#
# 7. IMPORTANT — After both services are deployed:
#    - Copy the frontend's public URL
#    - Go back to the backend service Variables
#    - Update CORS_ORIGINS and FRONTEND_URL with the actual frontend URL
#    - Railway will auto-redeploy
#
# 8. CUSTOM DOMAIN (optional):
#    - Frontend service → Settings → Custom Domain → Add heroichifi.org
#    - Follow DNS instructions Railway provides
#    - Update backend CORS_ORIGINS and FRONTEND_URL to match
#
# COST: ~$5/month total on Hobby tier (includes $5 credits)
# ================================================
