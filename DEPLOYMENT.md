# Deployment Guide for MP Groundwater Monitor

## Deployment to rudrajadon.in/mpgroundwatermonitor

### Prerequisites
- Node.js 18+ and npm installed
- Python 3.9+ for backend
- Docker and Docker Compose (optional)
- Access to the server with SSH
- Domain configured to point to your server

---

## Configuration Changes

### 1. Frontend Configuration

The app is configured to run at `/mpgroundwatermonitor` subpath:

**`frontend/next.config.js`:**
```javascript
basePath: '/mpgroundwatermonitor',
assetPrefix: '/mpgroundwatermonitor',
```

### 2. Environment Variables

**Frontend (`frontend/.env.production`):**
```env
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
```

**Backend (`backend/.env.production`):**
```env
DATABASE_URL=your_database_connection_string
CORS_ORIGINS=https://rudrajadon.in
```

---

## Deployment Options

### Option 1: Docker Deployment (Recommended)

1. **Create Docker Compose file** (`docker-compose.prod.yml`):

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: gw-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CORS_ORIGINS=https://rudrajadon.in
    volumes:
      - ./GW_Data:/app/GW_Data
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: gw-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
    depends_on:
      - backend
    restart: unless-stopped
```

2. **Create Frontend Dockerfile** (`frontend/Dockerfile.prod`):

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

3. **Build and Deploy:**

```bash
# On your server
cd /path/to/groundwater-app

# Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

### Option 2: PM2 Deployment

1. **Install PM2:**
```bash
npm install -g pm2
```

2. **Build Frontend:**
```bash
cd frontend
npm install
npm run build
```

3. **Create PM2 ecosystem file** (`ecosystem.config.js`):

```javascript
module.exports = {
  apps: [
    {
      name: 'gw-backend',
      cwd: './backend',
      script: 'uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8000',
      interpreter: 'python3',
      env: {
        DATABASE_URL: 'your_database_url',
        CORS_ORIGINS: 'https://rudrajadon.in'
      }
    },
    {
      name: 'gw-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'start',
      env: {
        PORT: 3000,
        NEXT_PUBLIC_API_BASE: 'https://rudrajadon.in/api/groundwater'
      }
    }
  ]
};
```

4. **Start with PM2:**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Enable on system boot
```

---

### Option 3: Nginx Reverse Proxy

**Nginx configuration** (`/etc/nginx/sites-available/rudrajadon.in`):

```nginx
server {
    listen 80;
    server_name rudrajadon.in;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name rudrajadon.in;

    ssl_certificate /etc/letsencrypt/live/rudrajadon.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rudrajadon.in/privkey.pem;

    # Frontend - MP Groundwater Monitor
    location /mpgroundwatermonitor {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/groundwater {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable and reload Nginx:**
```bash
sudo ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d rudrajadon.in -d www.rudrajadon.in

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

---

## Deployment Steps Summary

### Quick Deploy:

1. **Update configurations:**
   ```bash
   cd /path/to/groundwater-app
   
   # Create production env file
   cat > frontend/.env.production << EOF
   NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
   EOF
   ```

2. **Build frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Start services:**
   ```bash
   # Using PM2
   pm2 start ecosystem.config.js
   
   # OR using Docker
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Configure Nginx and SSL:**
   ```bash
   sudo nano /etc/nginx/sites-available/rudrajadon.in
   # Add configuration above
   
   sudo ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/
   sudo certbot --nginx -d rudrajadon.in
   sudo systemctl reload nginx
   ```

5. **Verify deployment:**
   ```bash
   # Check frontend
   curl https://rudrajadon.in/mpgroundwatermonitor
   
   # Check backend
   curl https://rudrajadon.in/api/groundwater/health
   ```

---

## Post-Deployment

### Monitoring:

```bash
# PM2 monitoring
pm2 monit
pm2 logs

# Docker monitoring
docker-compose -f docker-compose.prod.yml logs -f
docker stats
```

### Updates:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
cd frontend && npm run build
pm2 restart gw-frontend

# Or with Docker
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## Troubleshooting

### Issue: 404 errors on refresh
**Solution:** Ensure `trailingSlash: true` in `next.config.js` and Nginx properly forwards all requests.

### Issue: API calls failing
**Solution:** Check CORS settings in backend and verify `NEXT_PUBLIC_API_BASE` environment variable.

### Issue: Static assets not loading
**Solution:** Verify `assetPrefix` in `next.config.js` and Nginx static file serving.

### Issue: Database connection errors
**Solution:** Check `DATABASE_URL` in backend environment variables and database accessibility.

---

## Access Your App

**Frontend:** https://rudrajadon.in/mpgroundwatermonitor
**API:** https://rudrajadon.in/api/groundwater

---

## Security Checklist

- ✅ SSL certificate installed
- ✅ Firewall configured (only 80, 443 open)
- ✅ Environment variables secured
- ✅ Database credentials protected
- ✅ CORS properly configured
- ✅ Regular backups scheduled
- ✅ Monitoring and logging enabled

---

For issues or questions, check the logs or contact the development team.
