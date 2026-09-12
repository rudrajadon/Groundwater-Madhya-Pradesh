# ⚡ Quick Start - Deploy in 30 Minutes

## You've bought rudrajadon.in - Let's deploy! 🚀

---

## 📋 What You Need

1. ✅ Domain: rudrajadon.in (Already purchased!)
2. ⏳ Server: DigitalOcean, AWS, or any VPS
3. ⏳ 30 minutes of your time

---

## 🎯 Three Quick Commands

Once your server is ready, deployment is just 3 commands:

```bash
# 1. Upload project
scp -r groundwater-app root@YOUR_SERVER_IP:/home/rudrajadon/projects/

# 2. SSH and deploy
ssh root@YOUR_SERVER_IP
cd /home/rudrajadon/projects/groundwater-app
./deploy.sh docker

# 3. Get SSL
certbot --nginx -d rudrajadon.in -d www.rudrajadon.in
```

Done! ✅

---

## 📖 Detailed Steps

### STEP 1: Get a Server (10 minutes)

**DigitalOcean (Recommended):**
1. Go to https://digitalocean.com
2. Sign up + add payment ($6/month)
3. Create Droplet:
   - Ubuntu 22.04
   - Basic - $6/month
   - Bangalore region
4. Copy the IP address

**Your server IP:** `___.___.___.___`

---

### STEP 2: Point Domain to Server (5 minutes)

**In your domain registrar (BigRock/GoDaddy):**

1. Login to your account
2. Go to DNS Management for rudrajadon.in
3. Add these records:

```
Type    Host    Value (Your Server IP)    TTL
A       @       123.45.67.89              3600
A       www     123.45.67.89              3600
```

4. Save and wait 5-10 minutes

**Test DNS:**
```bash
ping rudrajadon.in
# Should show your server IP
```

---

### STEP 3: Setup Server (5 minutes)

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Run setup (one command)
curl -fsSL https://get.docker.com | sh && \
apt install -y docker-compose nginx certbot python3-certbot-nginx && \
mkdir -p /home/rudrajadon/projects
```

---

### STEP 4: Upload & Deploy (10 minutes)

**On your Mac:**
```bash
cd /Users/rudrajadon/Downloads

# Upload project
scp -r groundwater-app root@YOUR_SERVER_IP:/home/rudrajadon/projects/
```

**On server:**
```bash
ssh root@YOUR_SERVER_IP
cd /home/rudrajadon/projects/groundwater-app

# Create environment file
cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
EOF

# Deploy with one command!
./deploy.sh docker
```

This will:
- ✅ Install dependencies
- ✅ Build frontend
- ✅ Start backend
- ✅ Configure Nginx
- ✅ Start all services

---

### STEP 5: Get SSL Certificate (5 minutes)

```bash
# On server
certbot --nginx -d rudrajadon.in -d www.rudrajadon.in

# Follow prompts:
# - Enter email
# - Agree to terms
# - Redirect HTTP to HTTPS? Yes
```

---

## 🎉 DONE!

Your app is now live at:
**https://rudrajadon.in/mpgroundwatermonitor**

---

## ✅ Verify Everything Works

```bash
# Check services
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test in browser
open https://rudrajadon.in/mpgroundwatermonitor
```

---

## 🔧 Troubleshooting

**App not loading?**
```bash
# Check if containers are running
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Restart
docker-compose -f docker-compose.prod.yml restart
```

**DNS not working?**
```bash
# Wait 10-30 minutes for propagation
# Check DNS
nslookup rudrajadon.in
```

**SSL fails?**
```bash
# Make sure DNS is working first
ping rudrajadon.in

# Open firewall
ufw allow 80/tcp
ufw allow 443/tcp

# Try again
certbot --nginx -d rudrajadon.in
```

---

## 📚 More Help

- Full guide: `DEPLOYMENT_STEPS.md`
- Detailed docs: `DEPLOYMENT.md`
- Multi-project: `MULTI_PROJECT_DEPLOYMENT.md`

---

**Need help? Just ask! 🚀**
