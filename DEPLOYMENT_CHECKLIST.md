# ✅ Deployment Checklist for rudrajadon.in

## Progress Tracker

```
[✓] Domain purchased: rudrajadon.in
[ ] Server ready
[ ] DNS configured
[ ] Project deployed
[ ] SSL installed
[ ] App live!
```

---

## 📝 Step-by-Step Checklist

### ☐ **STEP 1: Get a Server (Choose One)**

#### Option A: DigitalOcean ($6/month - Recommended)
- [ ] Go to https://digitalocean.com
- [ ] Create account
- [ ] Add payment method
- [ ] Create Droplet:
  - [ ] Choose: Ubuntu 22.04 LTS
  - [ ] Choose: Basic $6/month (1GB RAM)
  - [ ] Choose: Bangalore datacenter
  - [ ] Set hostname: groundwater-monitor
- [ ] Copy server IP address: `___.___.___.___ `
- [ ] Save root password (will be emailed)

#### Option B: AWS EC2 (Free tier - 1 year free)
- [ ] Go to https://aws.amazon.com/free
- [ ] Create account
- [ ] Launch EC2 instance:
  - [ ] Choose: Ubuntu Server 22.04 LTS
  - [ ] Choose: t2.micro (free tier)
  - [ ] Create/download key pair
- [ ] Get Elastic IP (important!)
- [ ] Copy server IP: `___.___.___.___ `

---

### ☐ **STEP 2: Configure DNS**

#### At Your Domain Registrar (BigRock/GoDaddy):
- [ ] Login to registrar account
- [ ] Go to DNS Management for rudrajadon.in
- [ ] Add A Record:
  - [ ] Type: A
  - [ ] Host: @
  - [ ] Value: YOUR_SERVER_IP
  - [ ] TTL: 3600
- [ ] Add A Record for www:
  - [ ] Type: A  
  - [ ] Host: www
  - [ ] Value: YOUR_SERVER_IP
  - [ ] TTL: 3600
- [ ] Save changes
- [ ] Wait 5-10 minutes

#### Verify DNS:
```bash
# On your Mac terminal:
ping rudrajadon.in
# Should show your server IP
```
- [ ] DNS resolves to correct IP

---

### ☐ **STEP 3: Connect to Server**

```bash
# SSH into your server
ssh root@YOUR_SERVER_IP
# Enter password when prompted
# Type 'yes' to accept fingerprint
```

- [ ] Successfully connected to server via SSH
- [ ] You see the server terminal prompt

---

### ☐ **STEP 4: Prepare Server**

Run these commands on the server:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Install Nginx
apt install nginx -y

# Install Certbot (for SSL)
apt install certbot python3-certbot-nginx -y

# Create project directory
mkdir -p /home/rudrajadon/projects

# Verify installations
docker --version
docker-compose --version
nginx -v
certbot --version
```

Checklist:
- [ ] System updated
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Nginx installed
- [ ] Certbot installed
- [ ] Project directory created

---

### ☐ **STEP 5: Upload Project to Server**

**On your Mac (new terminal, NOT on server):**

```bash
cd /Users/rudrajadon/Downloads

# Upload entire project
scp -r groundwater-app root@YOUR_SERVER_IP:/home/rudrajadon/projects/
# This will take a few minutes
```

- [ ] Project uploaded successfully
- [ ] No errors during upload

---

### ☐ **STEP 6: Configure Environment**

**Back on server SSH terminal:**

```bash
cd /home/rudrajadon/projects/groundwater-app

# Create frontend environment file
cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
EOF

# Create backend environment file
cat > backend/.env << 'EOF'
DATABASE_URL=sqlite:///./groundwater.db
CORS_ORIGINS=https://rudrajadon.in
ENVIRONMENT=production
EOF

# Verify files created
ls -la frontend/.env.production
ls -la backend/.env
```

- [ ] frontend/.env.production created
- [ ] backend/.env created
- [ ] Both files have correct content

---

### ☐ **STEP 7: Deploy Application**

**Still on server:**

```bash
cd /home/rudrajadon/projects/groundwater-app

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh docker
```

This will take 5-10 minutes. You'll see:
- Dependencies installing
- Docker images building
- Containers starting
- Nginx configuring

Checklist:
- [ ] Deployment script completed without errors
- [ ] Containers started successfully
- [ ] No error messages in output

**Verify containers running:**
```bash
docker ps
# Should show: gw-frontend-prod and gw-backend-prod
```

- [ ] Both containers are running

---

### ☐ **STEP 8: Configure Nginx**

**On server:**

```bash
cd /home/rudrajadon/projects/groundwater-app

# Copy Nginx config
cp nginx.conf /etc/nginx/sites-available/rudrajadon.in

# Enable site
ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t
# Should say "test is successful"

# Reload Nginx
systemctl reload nginx
```

- [ ] Nginx config copied
- [ ] Site enabled
- [ ] Nginx test passed
- [ ] Nginx reloaded successfully

---

### ☐ **STEP 9: Test HTTP Access**

**On your Mac, open browser:**
```
http://rudrajadon.in
```

Or test from terminal:
```bash
curl http://rudrajadon.in
```

- [ ] Website loads (even without HTTPS)
- [ ] No 502 Bad Gateway error
- [ ] No connection refused error

---

### ☐ **STEP 10: Install SSL Certificate**

**On server:**

```bash
# Run Certbot
certbot --nginx -d rudrajadon.in -d www.rudrajadon.in
```

Follow the prompts:
```
1. Enter email: your_email@example.com
2. Agree to terms: Y
3. Share email with EFF: N (optional)
4. Redirect HTTP to HTTPS: 2 (Yes)
```

- [ ] SSL certificate obtained
- [ ] Nginx configured for HTTPS
- [ ] No errors from Certbot

**Test auto-renewal:**
```bash
certbot renew --dry-run
```
- [ ] Renewal test successful

---

### ☐ **STEP 11: Final Verification**

#### Test HTTPS Access:
**Open in browser:**
```
https://rudrajadon.in/mpgroundwatermonitor
```

- [ ] ✅ Site loads with HTTPS (padlock icon)
- [ ] ✅ No SSL warnings
- [ ] ✅ Map displays correctly
- [ ] ✅ Can click on wells and see data
- [ ] ✅ Charts load properly
- [ ] ✅ Mobile responsive works

#### Test API:
```bash
curl https://rudrajadon.in/api/groundwater/wells
```
- [ ] ✅ API returns data (JSON)

#### Check Logs:
```bash
# On server
docker-compose -f docker-compose.prod.yml logs -f
# Press Ctrl+C to exit
```
- [ ] ✅ No error messages
- [ ] ✅ Application running smoothly

---

## 🎉 **SUCCESS!**

If all checkboxes are marked, your deployment is complete!

**Your app is live at:**
### https://rudrajadon.in/mpgroundwatermonitor

---

## 📊 Post-Deployment Tasks

### Setup Monitoring:
```bash
# On server, check status anytime:
docker ps
docker stats
pm2 monit  # if using PM2
```

- [ ] Bookmark monitoring commands
- [ ] Know how to check logs
- [ ] Know how to restart services

### Document Your Deployment:
- [ ] Save server IP address
- [ ] Save SSH credentials
- [ ] Document any custom configurations
- [ ] Update GitHub README with live link

### Share Your Work:
- [ ] Add to portfolio
- [ ] Share on LinkedIn
- [ ] Update resume with live link
- [ ] Share with friends/colleagues

---

## 🔄 Common Maintenance Tasks

### Check Application Status:
```bash
ssh root@YOUR_SERVER_IP
docker ps
docker-compose -f /home/rudrajadon/projects/groundwater-app/docker-compose.prod.yml ps
```

### View Logs:
```bash
cd /home/rudrajadon/projects/groundwater-app
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Application:
```bash
cd /home/rudrajadon/projects/groundwater-app
docker-compose -f docker-compose.prod.yml restart
```

### Update Application:
```bash
cd /home/rudrajadon/projects/groundwater-app
git pull origin main  # if using Git
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🆘 Troubleshooting Reference

### If site doesn't load:
```bash
# Check containers
docker ps

# Check Nginx
systemctl status nginx

# Check logs
docker-compose logs
```

### If SSL fails:
```bash
# Verify DNS first
ping rudrajadon.in

# Try certbot again
certbot --nginx -d rudrajadon.in
```

### If need to restart everything:
```bash
docker-compose -f docker-compose.prod.yml restart
systemctl restart nginx
```

---

## 📚 Documentation Reference

- **Quick Start:** `QUICK_START.md`
- **Detailed Steps:** `DEPLOYMENT_STEPS.md`
- **Full Deployment:** `DEPLOYMENT.md`
- **Multi-Project:** `MULTI_PROJECT_DEPLOYMENT.md`
- **Troubleshooting:** `DEPLOYMENT.md` (Common Issues section)

---

## ✅ **DEPLOYMENT COMPLETE!**

Congratulations! 🎉 

Your MP Groundwater Monitor is now live and accessible worldwide!

**Live URL:** https://rudrajadon.in/mpgroundwatermonitor

---

**Need help with any step? Let me know!** 🚀
