# 🚀 MP Groundwater Monitor - Live Deployment Guide

## Congratulations on buying rudrajadon.in! 🎉

Let's deploy your first project: MP Groundwater Monitor

---

## 📋 Pre-Deployment Checklist

- [x] Domain purchased: rudrajadon.in ✅
- [ ] Server/VPS ready
- [ ] DNS configured
- [ ] Code ready to deploy
- [ ] Environment variables set

---

## 🎯 Deployment Options

Choose ONE of the following based on your preference:

### **Option A: DigitalOcean (Recommended - Easy)**
- Best for beginners
- Great documentation
- $6/month (₹500/month)
- Student? Get $200 free credit!

### **Option B: AWS EC2 (Free Tier)**
- Free for 1 year
- More complex setup
- Good for learning AWS

### **Option C: Local Server (If you have one)**
- Use your own machine/server
- Need static IP
- Port forwarding required

---

## 🚀 STEP-BY-STEP DEPLOYMENT

---

## STEP 1: Setup Server (Choose your option)

### Option A: DigitalOcean Setup

#### 1.1 Create Account
```
1. Go to: https://www.digitalocean.com/
2. Sign up with email
3. Verify email
4. Add payment method (will charge $6)

Student? Apply for GitHub Student Pack first:
- Go to: https://education.github.com/pack
- Get $200 DigitalOcean credit!
```

#### 1.2 Create Droplet
```
1. Click "Create" → "Droplets"
2. Choose region: Bangalore (closest to you)
3. Choose image: Ubuntu 22.04 LTS
4. Choose size: Basic - $6/month (1GB RAM, 1 CPU, 25GB SSD)
5. Authentication: SSH Key (recommended) or Password
6. Hostname: groundwater-monitor
7. Click "Create Droplet"
8. Wait 1-2 minutes
9. Copy the IP address shown
```

#### 1.3 SSH into Server
```bash
# If using password:
ssh root@YOUR_SERVER_IP

# If using SSH key:
ssh -i ~/.ssh/your_key root@YOUR_SERVER_IP

# Accept fingerprint: yes
```

---

## STEP 2: Configure DNS (Point Domain to Server)

### 2.1 Get Your Server IP
```
From DigitalOcean dashboard, copy the droplet IP address
Example: 123.45.67.89
```

### 2.2 Configure DNS at Domain Registrar

**If you bought from BigRock:**
```
1. Login to BigRock.in
2. Go to "Domain Management"
3. Click on rudrajadon.in
4. Click "Manage DNS" or "DNS Management"
5. Add/Edit these records:

   Type    Host    Value              TTL
   ----    ----    -----              ---
   A       @       YOUR_SERVER_IP     3600
   A       www     YOUR_SERVER_IP     3600

6. Save changes
7. Wait 5-10 minutes for DNS propagation
```

**If you bought from GoDaddy:**
```
1. Login to GoDaddy.com
2. Go to "My Products" → "Domains"
3. Click rudrajadon.in → "Manage DNS"
4. Edit/Add A records:

   Type    Name    Value              TTL
   ----    ----    -----              ---
   A       @       YOUR_SERVER_IP     1 Hour
   A       www     YOUR_SERVER_IP     1 Hour

5. Save
6. Wait 5-10 minutes
```

### 2.3 Verify DNS
```bash
# On your Mac, wait 5-10 minutes then check:
ping rudrajadon.in
# Should show your server IP

# Or use:
nslookup rudrajadon.in
# Should return your server IP
```

---

## STEP 3: Prepare Server

### 3.1 Update System
```bash
# SSH into your server first
ssh root@YOUR_SERVER_IP

# Then run:
apt update && apt upgrade -y
```

### 3.2 Install Docker (Recommended Method)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

**OR**

### 3.2 Alternative: Install Node.js + Python + PM2
```bash
# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Python 3 and pip
apt install -y python3 python3-pip python3-venv

# Install PM2
npm install -g pm2

# Verify
node --version
python3 --version
pm2 --version
```

### 3.3 Install Nginx
```bash
apt install nginx -y
systemctl enable nginx
systemctl start nginx

# Verify
nginx -v
```

### 3.4 Install Certbot (for SSL)
```bash
apt install certbot python3-certbot-nginx -y
```

---

## STEP 4: Upload Project Files

### Method A: Using Git (Recommended)
```bash
# On server, create directory
mkdir -p /home/rudrajadon/projects
cd /home/rudrajadon/projects

# Clone your repository
# If your code is on GitHub:
git clone YOUR_GITHUB_REPO_URL groundwater-app

# If not on GitHub yet, use Method B below
```

### Method B: Using SCP (from your Mac)
```bash
# On your Mac terminal (NOT on server):
cd /Users/rudrajadon/Downloads

# Copy entire project to server
scp -r groundwater-app root@YOUR_SERVER_IP:/home/rudrajadon/projects/

# This will take a few minutes depending on project size
```

---

## STEP 5: Configure Environment Variables

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Navigate to project
cd /home/rudrajadon/projects/groundwater-app

# Create frontend environment file
cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
EOF

# Create backend environment file (if needed)
cat > backend/.env << 'EOF'
DATABASE_URL=sqlite:///./groundwater.db
CORS_ORIGINS=https://rudrajadon.in
ENVIRONMENT=production
EOF

# Verify files created
cat frontend/.env.production
cat backend/.env
```

---

## STEP 6: Deploy Application

### Method A: Docker Deployment (Easier)

```bash
# On server, in project directory
cd /home/rudrajadon/projects/groundwater-app

# Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# This will take 5-10 minutes on first build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
# Press Ctrl+C to exit logs

# Check if containers are running
docker ps
# You should see gw-frontend-prod and gw-backend-prod
```

### Method B: PM2 Deployment

```bash
# On server, in project directory
cd /home/rudrajadon/projects/groundwater-app

# Install backend dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Start with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Copy and run the command it outputs

# Check status
pm2 status
pm2 logs
```

---

## STEP 7: Configure Nginx

### 7.1 Copy Nginx Configuration
```bash
# On server
cd /home/rudrajadon/projects/groundwater-app

# Copy the single-project nginx config
cp nginx.conf /etc/nginx/sites-available/rudrajadon.in

# Create symbolic link
ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# If test passes, reload Nginx
systemctl reload nginx
```

### 7.2 Test HTTP Access
```bash
# On your Mac, open browser:
http://rudrajadon.in

# Or test from terminal:
curl http://rudrajadon.in
```

---

## STEP 8: Setup SSL Certificate

```bash
# On server, run certbot
certbot --nginx -d rudrajadon.in -d www.rudrajadon.in

# Follow prompts:
# 1. Enter email address
# 2. Agree to terms (Y)
# 3. Share email (N is fine)
# 4. Choose redirect HTTP to HTTPS (2)

# Certbot will automatically:
# - Get SSL certificate
# - Configure Nginx for HTTPS
# - Setup auto-renewal

# Test auto-renewal
certbot renew --dry-run
```

---

## STEP 9: Verify Deployment

### 9.1 Check All Services
```bash
# Check Nginx
systemctl status nginx

# Check Docker containers (if using Docker)
docker ps

# Check PM2 processes (if using PM2)
pm2 status

# Check ports
netstat -tulpn | grep -E '(3000|8000|80|443)'
```

### 9.2 Test Your Application

**Open in browser:**
```
https://rudrajadon.in/mpgroundwatermonitor
```

**Test API:**
```bash
curl https://rudrajadon.in/api/groundwater/wells
```

### 9.3 Check Logs
```bash
# Docker logs
docker-compose -f docker-compose.prod.yml logs -f

# PM2 logs
pm2 logs

# Nginx logs
tail -f /var/log/nginx/groundwater-access.log
tail -f /var/log/nginx/groundwater-error.log
```

---

## ✅ SUCCESS CHECKLIST

- [ ] Domain DNS pointing to server ✓
- [ ] Server accessible via SSH ✓
- [ ] Docker/PM2 installed ✓
- [ ] Nginx installed ✓
- [ ] Project files uploaded ✓
- [ ] Environment variables configured ✓
- [ ] Application deployed ✓
- [ ] Nginx configured ✓
- [ ] SSL certificate installed ✓
- [ ] https://rudrajadon.in/mpgroundwatermonitor works! ✓

---

## 🎉 CONGRATULATIONS!

Your MP Groundwater Monitor is now LIVE at:
**https://rudrajadon.in/mpgroundwatermonitor**

---

## 🔧 Common Issues & Solutions

### Issue 1: Can't SSH into server
```bash
# Make sure you're using correct IP and credentials
# If using SSH key, check permissions:
chmod 600 ~/.ssh/your_key

# Try verbose mode to see what's wrong:
ssh -v root@YOUR_SERVER_IP
```

### Issue 2: DNS not resolving
```bash
# Wait 10-30 minutes for DNS propagation
# Check DNS:
nslookup rudrajadon.in

# If still not working, verify DNS records at registrar
```

### Issue 3: Containers won't start
```bash
# Check logs:
docker-compose -f docker-compose.prod.yml logs

# Check if ports are already in use:
netstat -tulpn | grep -E '(3000|8000)'

# Restart containers:
docker-compose -f docker-compose.prod.yml restart
```

### Issue 4: "502 Bad Gateway"
```bash
# Backend not running or not accessible

# Check if backend is running:
docker ps
# OR
pm2 status

# Check backend logs:
docker-compose -f docker-compose.prod.yml logs backend
# OR
pm2 logs gw-backend

# Restart services:
docker-compose -f docker-compose.prod.yml restart backend
# OR
pm2 restart gw-backend
```

### Issue 5: SSL certificate fails
```bash
# Make sure DNS is resolving first
ping rudrajadon.in

# Make sure port 80 is open
ufw allow 80/tcp
ufw allow 443/tcp

# Try again
certbot --nginx -d rudrajadon.in -d www.rudrajadon.in
```

---

## 📊 Monitoring Your Application

### View Logs
```bash
# Real-time logs (Docker)
docker-compose -f docker-compose.prod.yml logs -f

# Real-time logs (PM2)
pm2 logs

# Nginx access logs
tail -f /var/log/nginx/groundwater-access.log
```

### Check Resource Usage
```bash
# Docker stats
docker stats

# System resources
htop
# Install if not available: apt install htop

# Disk space
df -h

# Memory usage
free -h
```

### Restart Services
```bash
# Restart Docker containers
docker-compose -f docker-compose.prod.yml restart

# Restart PM2 processes
pm2 restart all

# Restart Nginx
systemctl restart nginx

# Reboot server (last resort)
reboot
```

---

## 🔄 Updating Your Application

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Navigate to project
cd /home/rudrajadon/projects/groundwater-app

# Pull latest code (if using Git)
git pull origin main

# Rebuild and restart (Docker)
docker-compose -f docker-compose.prod.yml up -d --build

# OR rebuild and restart (PM2)
cd frontend && npm run build && cd ..
pm2 restart ecosystem.config.js
```

---

## 🆘 Need Help?

If you encounter any issues:
1. Check the logs (see Monitoring section)
2. Review the Common Issues section above
3. Check DEPLOYMENT.md for more details
4. Ask me for help with specific error messages

---

## 📱 Share Your Work!

Your app is now live! Share it:
- **Portfolio:** https://rudrajadon.in/mpgroundwatermonitor
- **LinkedIn:** Post about your deployment
- **Resume:** Add the live link
- **GitHub:** Update README with live link

---

Good luck! 🚀
