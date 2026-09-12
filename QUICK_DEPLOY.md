# Quick Deployment Guide

## 🚀 Deploy to rudrajadon.in/mpgroundwatermonitor

### Option 1: Automated Deployment Script (Recommended)

```bash
# Make script executable
chmod +x deploy.sh

# Deploy with Docker
./deploy.sh docker

# OR Deploy with PM2
./deploy.sh pm2
```

### Option 2: Manual Docker Deployment

```bash
# 1. Create environment file
cat > frontend/.env.production << EOF
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
EOF

# 2. Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Check status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### Option 3: Manual PM2 Deployment

```bash
# 1. Install PM2
npm install -g pm2

# 2. Create environment file
cat > frontend/.env.production << EOF
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
EOF

# 3. Build frontend
cd frontend
npm install
npm run build
cd ..

# 4. Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## 🔧 Configure Nginx

```bash
# 1. Copy Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/rudrajadon.in

# 2. Enable site
sudo ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/

# 3. Test configuration
sudo nginx -t

# 4. Reload Nginx
sudo systemctl reload nginx
```

---

## 🔒 Setup SSL (Let's Encrypt)

```bash
# 1. Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 2. Get SSL certificate
sudo certbot --nginx -d rudrajadon.in -d www.rudrajadon.in

# 3. Auto-renewal is already configured by certbot
sudo certbot renew --dry-run
```

---

## ✅ Verify Deployment

```bash
# Check frontend
curl https://rudrajadon.in/mpgroundwatermonitor

# Check backend
curl https://rudrajadon.in/api/groundwater/health

# Check containers (Docker)
docker-compose -f docker-compose.prod.yml ps

# Check processes (PM2)
pm2 status
```

---

## 📊 Monitoring

### Docker:
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f backend

# Resource usage
docker stats
```

### PM2:
```bash
# View logs
pm2 logs

# Monitor processes
pm2 monit

# Process status
pm2 status
```

---

## 🔄 Updates and Maintenance

### Update Application:

```bash
# Pull latest code
git pull origin main

# Docker: Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# PM2: Rebuild frontend and restart
cd frontend && npm run build && cd ..
pm2 restart ecosystem.config.js
```

### Stop Application:

```bash
# Docker
docker-compose -f docker-compose.prod.yml down

# PM2
pm2 stop ecosystem.config.js
```

---

## 🆘 Troubleshooting

### Issue: Port already in use
```bash
# Check what's using the port
sudo lsof -i :3000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

### Issue: Permission denied
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x deploy.sh
```

### Issue: Frontend not loading
```bash
# Check Next.js build
cd frontend
npm run build

# Check environment variables
cat .env.production

# Verify basePath in next.config.js
cat next.config.js
```

### Issue: API calls failing
```bash
# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend
# OR
pm2 logs gw-backend

# Verify CORS settings
# Check backend/.env for CORS_ORIGINS
```

---

## 📱 Access Your Application

**🌐 Frontend:** https://rudrajadon.in/mpgroundwatermonitor

**🔌 API:** https://rudrajadon.in/api/groundwater

---

## 📝 Configuration Files Created

- ✅ `next.config.js` - Updated with basePath
- ✅ `DEPLOYMENT.md` - Full deployment guide
- ✅ `deploy.sh` - Automated deployment script
- ✅ `ecosystem.config.js` - PM2 configuration
- ✅ `nginx.conf` - Nginx configuration
- ✅ `docker-compose.prod.yml` - Docker Compose for production
- ✅ `frontend/Dockerfile.prod` - Production Docker image

---

## 🎯 Key Configuration Changes

### Frontend (next.config.js):
```javascript
basePath: '/mpgroundwatermonitor',
assetPrefix: '/mpgroundwatermonitor',
output: 'standalone',  // For Docker
trailingSlash: true,
```

### Environment Variables:
```env
# Frontend
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater

# Backend
CORS_ORIGINS=https://rudrajadon.in
```

---

Need help? Check `DEPLOYMENT.md` for detailed documentation.
