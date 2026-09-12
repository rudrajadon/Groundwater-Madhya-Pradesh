# 🔧 Fix API URL Configuration

## Problem
Backend API routes return 404 because the URL is doubled:
- Current: `https://...onrender.com/api/api/v1/wells` ❌
- Correct: `https://...onrender.com/api/v1/wells` ✅

## Solution

### 1. Update Local File (Already Done)
✅ Changed `frontend/.env.production` to:
```
NEXT_PUBLIC_API_BASE=https://mp-groundwater-backend.onrender.com
```

### 2. Update Vercel Environment Variable

#### In Vercel Dashboard:

1. Go to your project: **groundwater-madhya-pradesh**
2. Click **Settings** → **Environment Variables**
3. Find: `NEXT_PUBLIC_API_BASE`
4. Click **Edit**
5. Change value to:
   ```
   https://mp-groundwater-backend.onrender.com
   ```
   (Remove the `/api` at the end)
6. Click **Save**

### 3. Redeploy

After changing the environment variable:

**Option A: Redeploy from Vercel Dashboard**
1. Go to **Deployments** tab
2. Click **"..."** on latest deployment
3. Click **"Redeploy"**

**Option B: Push to GitHub (will auto-deploy)**
```bash
cd /Users/rudrajadon/Downloads/groundwater-app

git add frontend/.env.production
git commit -m "Fix: Correct API base URL to avoid double /api path"
git push origin main
```

---

## 🧪 Test After Deployment

### Test Backend Directly:
```
https://mp-groundwater-backend.onrender.com/api/v1/wells
```
Should return JSON with wells data ✅

### Test Frontend:
```
https://groundwater-madhya-pradesh.vercel.app/mpgroundwatermonitor
```
Should load map with wells ✅

---

## ✅ Expected Result

Frontend will call:
```
API_BASE = "https://mp-groundwater-backend.onrender.com"
getWells() → fetch(`${API_BASE}/api/v1/wells`)
         → "https://mp-groundwater-backend.onrender.com/api/v1/wells" ✅
```

NOT:
```
API_BASE = "https://mp-groundwater-backend.onrender.com/api"
getWells() → fetch(`${API_BASE}/api/v1/wells`)
         → "https://mp-groundwater-backend.onrender.com/api/api/v1/wells" ❌
```
