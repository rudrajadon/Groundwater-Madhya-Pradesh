# 🌐 Multi-Project Deployment on rudrajadon.in

## Architecture Overview

```
rudrajadon.in/
├── /                          → Landing page / Portfolio
├── /mpgroundwatermonitor/     → MP Groundwater Monitor (Project 1)
├── /project2/                 → Your Project 2
└── /project3/                 → Your Project 3
```

Or subdomain approach:
```
rudrajadon.in/                 → Landing page / Portfolio
mpgroundwater.rudrajadon.in/   → MP Groundwater Monitor
project2.rudrajadon.in/        → Project 2
project3.rudrajadon.in/        → Project 3
```

---

## 📋 **Recommended Approach: Subpath Method**

### Pros:
- ✅ Single SSL certificate
- ✅ Simpler DNS setup
- ✅ Better for portfolio (all under one domain)
- ✅ Easier Nginx configuration

### Cons:
- ⚠️ Each app needs basePath configuration
- ⚠️ Slightly more Nginx config

---

## 🔧 **Complete Nginx Configuration for 3 Projects**

### nginx-multi-project.conf

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name rudrajadon.in www.rudrajadon.in;
    return 301 https://$host$request_uri;
}

# Main HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name rudrajadon.in www.rudrajadon.in;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/rudrajadon.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rudrajadon.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/rudrajadon-access.log;
    error_log /var/log/nginx/rudrajadon-error.log;

    # ============================================
    # Root / Landing Page (Portfolio)
    # ============================================
    location / {
        root /var/www/rudrajadon.in;
        index index.html index.htm;
        try_files $uri $uri/ =404;
    }

    # ============================================
    # Project 1: MP Groundwater Monitor
    # ============================================
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

    # MP Groundwater API
    location /api/groundwater {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ============================================
    # Project 2: Your Second Project
    # ============================================
    location /project2 {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Project 2 API (if needed)
    location /api/project2 {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ============================================
    # Project 3: Your Third Project
    # ============================================
    location /project3 {
        proxy_pass http://localhost:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Project 3 API (if needed)
    location /api/project3 {
        proxy_pass http://localhost:8002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ============================================
    # Static files caching
    # ============================================
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
}
```

---

## 🎯 **Port Allocation Strategy**

| Project | Frontend Port | Backend Port | Path |
|---------|--------------|--------------|------|
| **Landing Page** | - | - | `/` |
| **MP Groundwater** | 3000 | 8000 | `/mpgroundwatermonitor` |
| **Project 2** | 3001 | 8001 | `/project2` |
| **Project 3** | 3002 | 8002 | `/project3` |

---

## 📦 **PM2 Configuration for All Projects**

### ecosystem-all-projects.config.js

```javascript
module.exports = {
  apps: [
    // ==========================================
    // Project 1: MP Groundwater Monitor
    // ==========================================
    {
      name: 'gw-backend',
      cwd: './projects/groundwater-app/backend',
      script: 'uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8000',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        DATABASE_URL: process.env.GW_DATABASE_URL,
        CORS_ORIGINS: 'https://rudrajadon.in'
      }
    },
    {
      name: 'gw-frontend',
      cwd: './projects/groundwater-app/frontend',
      script: 'npm',
      args: 'start',
      instances: 1,
      autorestart: true,
      env: {
        PORT: 3000,
        NEXT_PUBLIC_API_BASE: 'https://rudrajadon.in/api/groundwater'
      }
    },

    // ==========================================
    // Project 2
    // ==========================================
    {
      name: 'project2-backend',
      cwd: './projects/project2/backend',
      script: 'your-backend-start-command',
      instances: 1,
      autorestart: true,
      env: {
        PORT: 8001,
        // Add your project 2 env vars
      }
    },
    {
      name: 'project2-frontend',
      cwd: './projects/project2/frontend',
      script: 'npm',
      args: 'start',
      instances: 1,
      autorestart: true,
      env: {
        PORT: 3001,
        // Add your project 2 env vars
      }
    },

    // ==========================================
    // Project 3
    // ==========================================
    {
      name: 'project3-backend',
      cwd: './projects/project3/backend',
      script: 'your-backend-start-command',
      instances: 1,
      autorestart: true,
      env: {
        PORT: 8002,
        // Add your project 3 env vars
      }
    },
    {
      name: 'project3-frontend',
      cwd: './projects/project3/frontend',
      script: 'npm',
      args: 'start',
      instances: 1,
      autorestart: true,
      env: {
        PORT: 3002,
        // Add your project 3 env vars
      }
    }
  ]
};
```

---

## 🐳 **Docker Compose for All Projects**

### docker-compose-all.yml

```yaml
version: '3.8'

services:
  # ==========================================
  # Project 1: MP Groundwater Monitor
  # ==========================================
  gw-backend:
    build: ./projects/groundwater-app/backend
    container_name: gw-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${GW_DATABASE_URL}
      - CORS_ORIGINS=https://rudrajadon.in
    restart: unless-stopped
    networks:
      - app-network

  gw-frontend:
    build: ./projects/groundwater-app/frontend
    container_name: gw-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
    depends_on:
      - gw-backend
    restart: unless-stopped
    networks:
      - app-network

  # ==========================================
  # Project 2
  # ==========================================
  project2-backend:
    build: ./projects/project2/backend
    container_name: project2-backend
    ports:
      - "8001:8001"
    environment:
      - PORT=8001
      # Add your env vars
    restart: unless-stopped
    networks:
      - app-network

  project2-frontend:
    build: ./projects/project2/frontend
    container_name: project2-frontend
    ports:
      - "3001:3001"
    environment:
      - PORT=3001
      # Add your env vars
    depends_on:
      - project2-backend
    restart: unless-stopped
    networks:
      - app-network

  # ==========================================
  # Project 3
  # ==========================================
  project3-backend:
    build: ./projects/project3/backend
    container_name: project3-backend
    ports:
      - "8002:8002"
    environment:
      - PORT=8002
      # Add your env vars
    restart: unless-stopped
    networks:
      - app-network

  project3-frontend:
    build: ./projects/project3/frontend
    container_name: project3-frontend
    ports:
      - "3002:3002"
    environment:
      - PORT=3002
      # Add your env vars
    depends_on:
      - project3-backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

---

## 🎨 **Create a Portfolio Landing Page**

### Simple Portfolio HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rudra Jadon - Portfolio</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            background: white;
            border-radius: 20px;
            padding: 60px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            font-size: 3rem;
            color: #333;
            margin-bottom: 20px;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 50px;
        }
        .projects {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
        .project-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            color: white;
            text-decoration: none;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .project-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        .project-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .project-desc {
            font-size: 0.95rem;
            opacity: 0.9;
        }
        .social-links {
            margin-top: 40px;
            display: flex;
            gap: 20px;
        }
        .social-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Rudra Jadon</h1>
        <p class="subtitle">Full Stack Developer | Data Scientist | ML Engineer</p>
        
        <div class="projects">
            <a href="/mpgroundwatermonitor" class="project-card">
                <div class="project-title">💧 MP Groundwater Monitor</div>
                <div class="project-desc">
                    Real-time groundwater level monitoring and forecasting system 
                    for Madhya Pradesh using ML models.
                </div>
            </a>
            
            <a href="/project2" class="project-card">
                <div class="project-title">🚀 Project 2</div>
                <div class="project-desc">
                    Description of your second project goes here.
                </div>
            </a>
            
            <a href="/project3" class="project-card">
                <div class="project-title">🎯 Project 3</div>
                <div class="project-desc">
                    Description of your third project goes here.
                </div>
            </a>
        </div>
        
        <div class="social-links">
            <a href="https://github.com/rudrajadon" class="social-link">GitHub</a>
            <a href="https://linkedin.com/in/rudrajadon" class="social-link">LinkedIn</a>
            <a href="mailto:rudra@rudrajadon.in" class="social-link">Email</a>
        </div>
    </div>
</body>
</html>
```

Save this as `/var/www/rudrajadon.in/index.html`

---

## 📂 **Folder Structure on Server**

```
/home/rudrajadon/
├── projects/
│   ├── groundwater-app/          # Project 1
│   │   ├── frontend/
│   │   └── backend/
│   ├── project2/                 # Project 2
│   │   ├── frontend/
│   │   └── backend/
│   └── project3/                 # Project 3
│       ├── frontend/
│       └── backend/
├── ecosystem-all-projects.config.js
└── docker-compose-all.yml

/var/www/rudrajadon.in/
└── index.html                    # Portfolio landing page
```

---

## 💰 **Cost Estimation**

### Annual Costs:
| Item | Cost (INR/year) |
|------|-----------------|
| **.in Domain** | ₹500-800 |
| **VPS/Cloud Server** | ₹3,000-12,000 |
| **SSL Certificate** | Free (Let's Encrypt) |
| **Total** | **₹3,500-12,800/year** |

### Server Recommendations:
- **Budget:** DigitalOcean Basic Droplet (₹400/month)
- **Medium:** Linode 4GB (₹700/month)
- **High:** AWS EC2 t3.medium (₹1,000/month)

---

## 🚀 **Deployment Steps**

### 1. Buy Domain
```
Register at: GoDaddy, Namecheap, BigRock, or any registrar
Cost: ~₹600-800/year for .in domain
```

### 2. Setup Server
```bash
# Get a VPS from DigitalOcean, Linode, or AWS
# Ubuntu 22.04 LTS recommended
# Minimum: 2GB RAM, 1 CPU, 25GB SSD
```

### 3. Point Domain to Server
```
In domain registrar DNS settings:
A Record: @ → Your_Server_IP
A Record: www → Your_Server_IP
```

### 4. Deploy All Projects
```bash
# Clone all projects
cd /home/rudrajadon
mkdir projects && cd projects
git clone your-repo-urls

# Start with PM2
pm2 start ecosystem-all-projects.config.js
pm2 save
pm2 startup

# Or with Docker
docker-compose -f docker-compose-all.yml up -d
```

### 5. Configure Nginx & SSL
```bash
sudo cp nginx-multi-project.conf /etc/nginx/sites-available/rudrajadon.in
sudo ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL
sudo certbot --nginx -d rudrajadon.in -d www.rudrajadon.in
```

---

## ✅ **Final URLs**

- **Portfolio:** https://rudrajadon.in/
- **Project 1:** https://rudrajadon.in/mpgroundwatermonitor/
- **Project 2:** https://rudrajadon.in/project2/
- **Project 3:** https://rudrajadon.in/project3/

---

## 🎯 **My Recommendation**

**YES, buy rudrajadon.in** because:
1. ✅ Professional personal branding
2. ✅ Single domain for portfolio + projects
3. ✅ Easy to manage (one SSL, one server)
4. ✅ Good for job applications/networking
5. ✅ Low cost (₹600-800/year)

**Alternative if budget is tight:**
- Use **Vercel** (free): project1.vercel.app, project2.vercel.app
- Use **Netlify** (free): project1.netlify.app
- Buy domain later when ready

---

Need help setting this up? Let me know! 🚀
