# 🚀 Deploy Now - 3 Simple Steps

Your app is ready to deploy! Follow these 3 steps:

---

## ✅ Prerequisites

- [x] Domain purchased: rudrajadon.in
- [x] Code ready
- [x] Git initialized
- [ ] GitHub account (create at https://github.com)

---

## 📦 STEP 1: Push to GitHub (2 minutes)

### 1.1 Create GitHub Repository

1. Go to: https://github.com/new
2. Repository name: `groundwater-app`
3. Public or Private (your choice)
4. **Don't** add README or .gitignore (we have them)
5. Click "Create repository"
6. Copy the repository URL (looks like: `https://github.com/YOUR_USERNAME/groundwater-app.git`)

### 1.2 Push Your Code

```bash
cd /Users/rudrajadon/Downloads/groundwater-app

# Add all files
git add .

# Commit
git commit -m "Initial commit - ready for deployment"

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/groundwater-app.git

# Push to GitHub
git push -u origin main
```

**✅ Done! Your code is on GitHub**

---

## 🐍 STEP 2: Deploy Backend to Render (5 minutes)

### 2.1 Sign Up for Render

1. Go to: https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended) or Email
4. Verify your email

### 2.2 Create Web Service

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Click **"Build and deploy from a Git repository"** → Next
3. Connect your GitHub account (if not already)
4. Select your `groundwater-app` repository
5. Click **"Connect"**

### 2.3 Configure Service

Fill in these settings:

```
Name: mp-groundwater-backend
Region: Singapore (closest to India)
Branch: main
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:** Free

### 2.4 Deploy

1. Scroll down and click **"Create Web Service"**
2. Wait 3-5 minutes (watch the logs)
3. Once deployed, you'll see: **"Your service is live 🎉"**
4. **IMPORTANT: Copy your backend URL**
   - Looks like: `https://mp-groundwater-backend.onrender.com`
   - Save this! You'll need it for the next step

### 2.5 Test Backend

Open in browser:
```
https://mp-groundwater-backend.onrender.com/wells
```

You should see JSON data! ✅

**✅ Backend is LIVE!**

---

## ⚡ STEP 3: Deploy Frontend to Vercel (5 minutes)

### 3.1 Create Environment File

```bash
cd /Users/rudrajadon/Downloads/groundwater-app/frontend

# Create .env.production file
cat > .env.production << 'EOF'
NEXT_PUBLIC_API_BASE=YOUR_RENDER_BACKEND_URL/api
EOF

# Replace YOUR_RENDER_BACKEND_URL with your actual URL from Step 2
# Example: https://mp-groundwater-backend.onrender.com/api
```

Or manually create `frontend/.env.production`:
```
NEXT_PUBLIC_API_BASE=https://mp-groundwater-backend.onrender.com/api
```

### 3.2 Commit and Push

```bash
cd /Users/rudrajadon/Downloads/groundwater-app

git add frontend/.env.production
git commit -m "Add production environment config"
git push origin main
```

### 3.3 Sign Up for Vercel

1. Go to: https://vercel.com
2. Click "Sign Up"
3. Choose **"Continue with GitHub"** (recommended)
4. Authorize Vercel to access GitHub

### 3.4 Import Project

1. In Vercel dashboard, click **"Add New..."** → **"Project"**
2. Find `groundwater-app` in the list
3. Click **"Import"**

### 3.5 Configure Project

```
Framework Preset: Next.js (should auto-detect)
Root Directory: frontend
Build Command: npm run build (auto-filled)
Output Directory: (leave default)
Install Command: npm install (auto-filled)
```

**Environment Variables:**
Click "Add" and enter:
```
Name: NEXT_PUBLIC_API_BASE
Value: https://mp-groundwater-backend.onrender.com/api
```
(Use your actual backend URL from Step 2)

### 3.6 Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes (watch the build logs)
3. You'll see: **"Congratulations! 🎉"**
4. Vercel gives you a URL like: `https://groundwater-app.vercel.app`
5. Click **"Visit"** to test your app!

**✅ Frontend is LIVE!**

---

## 🌐 BONUS: Connect Your Domain (2 minutes)

### 4.1 Add Domain in Vercel

1. In your project dashboard, click **"Settings"** → **"Domains"**
2. Enter: `rudrajadon.in`
3. Click "Add"
4. Vercel will show DNS configuration needed

### 4.2 Configure DNS

You have 2 options:

#### Option A: Use Vercel's DNS (Easiest)
Vercel shows you nameservers:
```
ns1.vercel-dns.com
ns2.vercel-dns.com
```

At your domain registrar:
1. Go to DNS settings
2. Change nameservers to Vercel's
3. Wait 10-30 minutes
4. Done! ✅

#### Option B: Keep Your DNS, Add Records
At your domain registrar, add:

**For Root Domain:**
```
Type: A
Name: @
Value: 76.76.19.61 (or IP Vercel provides)
```

**For www:**
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

### 4.3 Configure Base Path (For /mpgroundwatermonitor)

Your app is already configured for the subpath!

In Vercel:
1. Go to Project Settings → General
2. The `basePath` from `next.config.js` is already set
3. Your app will be at: `rudrajadon.in/mpgroundwatermonitor` ✅

### 4.4 Wait for DNS Propagation

- Takes 5-30 minutes
- Vercel auto-detects when ready
- Automatic SSL certificate
- You'll see "Valid Configuration" ✅

---

## 🎉 SUCCESS!

Your MP Groundwater Monitor is now LIVE at:

### **https://rudrajadon.in/mpgroundwatermonitor**

or

### **https://groundwater-app.vercel.app/mpgroundwatermonitor**

---

## 📊 What You Have Now

✅ **Frontend:** Hosted on Vercel (FREE)
✅ **Backend:** Hosted on Render (FREE)
✅ **Domain:** rudrajadon.in (Connected)
✅ **SSL:** Automatic HTTPS
✅ **Auto-Deploy:** Push to GitHub = Auto-deploy!

---

## 🔄 Future Updates

To update your app:

```bash
cd /Users/rudrajadon/Downloads/groundwater-app

# Make your changes...

git add .
git commit -m "Update: description of changes"
git push origin main
```

**Both Vercel and Render auto-deploy on push!** 🚀

---

## 📱 Share Your Work

Your app is live! Share it:

- **Portfolio:** https://rudrajadon.in/mpgroundwatermonitor
- **LinkedIn:** "Built and deployed MP Groundwater Monitoring System"
- **Resume:** Add as project with live link
- **GitHub:** Add live link to README

---

## 🆘 Troubleshooting

### Backend shows 404:
- Check backend deployed successfully on Render
- Check backend URL is correct
- Check `/wells` endpoint works

### Frontend can't connect to backend:
- Check `NEXT_PUBLIC_API_BASE` in Vercel environment variables
- Should be: `https://YOUR-BACKEND.onrender.com/api`
- Redeploy frontend after changing env vars

### Backend is slow (first request):
- Render free tier: Sleeps after 15 min of inactivity
- First request takes ~30 seconds to wake up
- Subsequent requests are fast
- **Solution:** Upgrade to paid ($7/month) or keep awake with cron job

### Domain not working:
- Wait 30 minutes for DNS propagation
- Check DNS records at registrar
- Use `nslookup rudrajadon.in` to verify

---

## 💰 Cost Breakdown

**Current (FREE):**
- Vercel: $0/month
- Render: $0/month (with sleep)
- Domain: ₹600/year (~₹50/month)
- **Total: ₹50/month**

**Upgrade (Optional):**
- Vercel: $0 (free tier is enough)
- Render: $7/month (no sleep, better performance)
- **Total: $7 + ₹50 = ~₹625/month**

---

## ✅ Final Checklist

- [ ] Code on GitHub
- [ ] Backend on Render (tested /wells endpoint)
- [ ] Frontend on Vercel (tested in browser)
- [ ] Domain connected
- [ ] SSL working (https://)
- [ ] App accessible at rudrajadon.in/mpgroundwatermonitor

---

## 🎓 What You Learned

✅ Git & GitHub
✅ Backend deployment (Render)
✅ Frontend deployment (Vercel)
✅ DNS & Domain configuration
✅ Environment variables
✅ CI/CD (auto-deployment)
✅ Free hosting solutions

---

**Congratulations! You've successfully deployed a full-stack geospatial application! 🎉**

Need help? Just ask! 🚀
