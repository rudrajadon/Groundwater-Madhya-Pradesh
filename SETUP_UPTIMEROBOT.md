# 🤖 Setup UptimeRobot Keep-Alive (FREE)

This keeps your Render backend awake 24/7 so users don't experience 30-second delays!

---

## 📝 Steps:

### 1. Go to UptimeRobot
https://uptimerobot.com

### 2. Sign Up (FREE)
- Click "Register for FREE"
- Enter email and create password
- Verify email

### 3. Add New Monitor
Once logged in:
1. Click **"+ Add New Monitor"**
2. Fill in:
   ```
   Monitor Type: HTTP(s)
   Friendly Name: MP Groundwater Backend
   URL (or IP): https://mp-groundwater-backend.onrender.com/health
   Monitoring Interval: 5 minutes
   ```
3. Click **"Create Monitor"**

---

## ✅ Done!

Your backend will now be pinged every 5 minutes, preventing it from sleeping!

**Benefits:**
- ✅ No more 30-second cold starts
- ✅ Users get instant responses
- ✅ 100% FREE
- ✅ Email alerts if backend goes down

---

## 📊 What This Does:

Before UptimeRobot:
```
User clicks well → Backend sleeping → 30 sec wake up → 3 sec ML → Response (33 seconds!)
```

After UptimeRobot:
```
User clicks well → Backend awake → 3 sec ML → Response (3 seconds!)
```

After Pre-calculation (next step):
```
User clicks well → Backend awake → Cached response → Instant! (<1 second!)
```

---

## 🔔 Optional: Setup Alerts

In UptimeRobot dashboard:
1. Go to "Alert Contacts"
2. Add your email
3. Get notified if your backend goes down

---

**This takes 2 minutes to set up and makes your app 10x faster!** 🚀
