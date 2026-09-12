# 🚀 MP Groundwater Monitor - Deployment Summary

## ✅ All Configured for: rudrajadon.in/mpgroundwatermonitor

---

## 📦 Files Created

| File | Purpose |
|------|---------|
| ✅ `DEPLOYMENT.md` | Complete deployment documentation |
| ✅ `QUICK_DEPLOY.md` | Quick start deployment guide |
| ✅ `deploy.sh` | Automated deployment script |
| ✅ `ecosystem.config.js` | PM2 process configuration |
| ✅ `nginx.conf` | Nginx reverse proxy config |
| ✅ `docker-compose.prod.yml` | Docker production setup |
| ✅ `frontend/Dockerfile.prod` | Frontend production image |
| ✅ `frontend/next.config.js` | Updated with basePath |

---

## 🎯 Configuration Applied

### Frontend Configuration
```javascript
// next.config.js
basePath: '/mpgroundwatermonitor'
assetPrefix: '/mpgroundwatermonitor'
output: 'standalone'
trailingSlash: true
```

### Environment Setup
```env
# Frontend
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater

# Backend  
CORS_ORIGINS=https://rudrajadon.in
```

---

## 🚀 Deployment Options

### Option 1: One-Command Deployment (Easiest)
```bash
./deploy.sh docker    # or ./deploy.sh pm2
```

### Option 2: Docker Compose
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Option 3: PM2
```bash
cd frontend && npm run build && cd ..
pm2 start ecosystem.config.js
```

---

## 🔧 Server Setup Required

### 1. Install Dependencies

**For Docker:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose
```

**For PM2:**
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2
npm install -g pm2

# Install Python & pip
sudo apt install python3 python3-pip
```

### 2. Configure Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/rudrajadon.in
sudo ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Setup SSL
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d rudrajadon.in -d www.rudrajadon.in
```

---

## 📍 URLs After Deployment

| Service | URL |
|---------|-----|
| **Frontend** | https://rudrajadon.in/mpgroundwatermonitor |
| **API** | https://rudrajadon.in/api/groundwater |
| **Health Check** | https://rudrajadon.in/health |

---

## 🔍 Testing Deployment

```bash
# Test frontend
curl https://rudrajadon.in/mpgroundwatermonitor

# Test backend
curl https://rudrajadon.in/api/groundwater/wells

# Check SSL
curl -I https://rudrajadon.in

# Check containers (Docker)
docker-compose -f docker-compose.prod.yml ps

# Check processes (PM2)
pm2 status
```

---

## 📊 Monitoring Commands

### Docker
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### PM2
```bash
# View logs
pm2 logs

# Monitor
pm2 monit

# Status
pm2 status

# Restart
pm2 restart ecosystem.config.js

# Stop
pm2 stop ecosystem.config.js
```

---

## 🔄 Update Workflow

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild
# Docker:
docker-compose -f docker-compose.prod.yml up -d --build

# PM2:
cd frontend && npm run build && cd ..
pm2 restart ecosystem.config.js
```

---

## 🆘 Quick Troubleshooting

### Frontend not loading
```bash
# Check build
cd frontend && npm run build

# Verify environment
cat frontend/.env.production

# Check Next.js config
cat frontend/next.config.js
```

### API not responding
```bash
# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend
# OR
pm2 logs gw-backend

# Test locally
curl http://localhost:8000/health
```

### SSL issues
```bash
# Renew certificate
sudo certbot renew

# Check certificate
sudo certbot certificates

# Test SSL
openssl s_client -connect rudrajadon.in:443
```

### Port conflicts
```bash
# Check what's using ports
sudo lsof -i :3000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

---

## 📋 Pre-Deployment Checklist

- [ ] Server accessible via SSH
- [ ] Domain DNS points to server IP
- [ ] Docker or Node.js+PM2 installed
- [ ] Nginx installed
- [ ] Firewall configured (ports 80, 443 open)
- [ ] Database configured (if using external DB)
- [ ] Environment variables set
- [ ] Deployment files copied to server

---

## 🎉 Post-Deployment Checklist

- [ ] Frontend accessible at https://rudrajadon.in/mpgroundwatermonitor
- [ ] API responding at https://rudrajadon.in/api/groundwater
- [ ] SSL certificate active
- [ ] All features working (maps, charts, data)
- [ ] Mobile responsive (test on devices)
- [ ] Logs are being generated
- [ ] Monitoring setup (PM2 or Docker)
- [ ] Auto-restart configured
- [ ] Backup strategy in place

---

## 📚 Documentation

- **Full Guide:** `DEPLOYMENT.md`
- **Quick Start:** `QUICK_DEPLOY.md`
- **This Summary:** `DEPLOYMENT_SUMMARY.md`

---

## 🤝 Support

For issues:
1. Check logs (Docker/PM2)
2. Review troubleshooting section
3. Check Nginx error logs: `/var/log/nginx/groundwater-error.log`
4. Verify environment variables
5. Test backend/frontend independently

---

## ⚡ Quick Commands Reference

```bash
# Deploy
./deploy.sh docker

# Check status
docker-compose -f docker-compose.prod.yml ps
pm2 status

# View logs
docker-compose -f docker-compose.prod.yml logs -f
pm2 logs

# Restart
docker-compose -f docker-compose.prod.yml restart
pm2 restart ecosystem.config.js

# Stop
docker-compose -f docker-compose.prod.yml down
pm2 stop ecosystem.config.js

# Update
git pull && ./deploy.sh docker
```

---

**🎯 Ready to Deploy!**

Your application is configured and ready for deployment to **rudrajadon.in/mpgroundwatermonitor**

Good luck! 🚀
