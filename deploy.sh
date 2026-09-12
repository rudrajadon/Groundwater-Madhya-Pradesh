#!/bin/bash

# MP Groundwater Monitor Deployment Script
# Usage: ./deploy.sh [docker|pm2]

set -e

DEPLOYMENT_TYPE=${1:-docker}
PROJECT_DIR=$(pwd)

echo "================================================"
echo "MP Groundwater Monitor - Deployment Script"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required commands exist
check_dependencies() {
    echo "Checking dependencies..."
    
    if [ "$DEPLOYMENT_TYPE" == "docker" ]; then
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Error: Docker is not installed${NC}"
            exit 1
        fi
        if ! command -v docker-compose &> /dev/null; then
            echo -e "${RED}Error: Docker Compose is not installed${NC}"
            exit 1
        fi
    elif [ "$DEPLOYMENT_TYPE" == "pm2" ]; then
        if ! command -v pm2 &> /dev/null; then
            echo -e "${RED}Error: PM2 is not installed. Install with: npm install -g pm2${NC}"
            exit 1
        fi
        if ! command -v node &> /dev/null; then
            echo -e "${RED}Error: Node.js is not installed${NC}"
            exit 1
        fi
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}Error: Python3 is not installed${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ All dependencies found${NC}"
}

# Create logs directory
create_logs_dir() {
    echo "Creating logs directory..."
    mkdir -p logs
    echo -e "${GREEN}✓ Logs directory created${NC}"
}

# Setup environment files
setup_env_files() {
    echo "Setting up environment files..."
    
    # Frontend .env.production
    if [ ! -f frontend/.env.production ]; then
        cat > frontend/.env.production << EOF
NEXT_PUBLIC_API_BASE=https://rudrajadon.in/api/groundwater
EOF
        echo -e "${GREEN}✓ Created frontend/.env.production${NC}"
    else
        echo -e "${YELLOW}⚠ frontend/.env.production already exists${NC}"
    fi
    
    # Backend .env (if needed)
    if [ ! -f backend/.env ]; then
        cat > backend/.env << EOF
DATABASE_URL=sqlite:///./groundwater.db
CORS_ORIGINS=https://rudrajadon.in
ENVIRONMENT=production
EOF
        echo -e "${GREEN}✓ Created backend/.env${NC}"
    else
        echo -e "${YELLOW}⚠ backend/.env already exists${NC}"
    fi
}

# Docker deployment
deploy_docker() {
    echo ""
    echo "================================================"
    echo "Deploying with Docker Compose"
    echo "================================================"
    echo ""
    
    # Stop existing containers
    echo "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Build and start containers
    echo "Building and starting containers..."
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Wait for services to be healthy
    echo "Waiting for services to start..."
    sleep 10
    
    # Check container status
    echo ""
    echo "Container status:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo -e "${GREEN}✓ Docker deployment complete!${NC}"
    echo ""
    echo "View logs with: docker-compose -f docker-compose.prod.yml logs -f"
    echo "Stop containers: docker-compose -f docker-compose.prod.yml down"
}

# PM2 deployment
deploy_pm2() {
    echo ""
    echo "================================================"
    echo "Deploying with PM2"
    echo "================================================"
    echo ""
    
    # Install backend dependencies
    echo "Installing backend dependencies..."
    cd backend
    pip3 install -r requirements.txt
    cd ..
    
    # Build frontend
    echo "Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Stop existing PM2 processes
    echo "Stopping existing PM2 processes..."
    pm2 delete ecosystem.config.js 2>/dev/null || true
    
    # Start PM2 processes
    echo "Starting PM2 processes..."
    pm2 start ecosystem.config.js
    
    # Save PM2 configuration
    pm2 save
    
    # Setup PM2 startup script
    echo ""
    echo "Setting up PM2 startup script..."
    pm2 startup
    
    echo ""
    echo -e "${GREEN}✓ PM2 deployment complete!${NC}"
    echo ""
    echo "View logs with: pm2 logs"
    echo "Monitor processes: pm2 monit"
    echo "Stop processes: pm2 stop ecosystem.config.js"
}

# Setup Nginx
setup_nginx() {
    echo ""
    echo "================================================"
    echo "Nginx Configuration"
    echo "================================================"
    echo ""
    
    if [ -f /etc/nginx/sites-available/rudrajadon.in ]; then
        echo -e "${YELLOW}⚠ Nginx configuration already exists at /etc/nginx/sites-available/rudrajadon.in${NC}"
        echo "Please review and update manually if needed"
    else
        echo "To setup Nginx:"
        echo "1. sudo cp nginx.conf /etc/nginx/sites-available/rudrajadon.in"
        echo "2. sudo ln -s /etc/nginx/sites-available/rudrajadon.in /etc/nginx/sites-enabled/"
        echo "3. sudo nginx -t"
        echo "4. sudo systemctl reload nginx"
    fi
}

# Setup SSL
setup_ssl() {
    echo ""
    echo "================================================"
    echo "SSL Certificate Setup"
    echo "================================================"
    echo ""
    
    echo "To setup SSL with Let's Encrypt:"
    echo "1. sudo apt install certbot python3-certbot-nginx"
    echo "2. sudo certbot --nginx -d rudrajadon.in -d www.rudrajadon.in"
    echo "3. Certbot will automatically configure SSL"
}

# Main deployment
main() {
    echo "Deployment type: $DEPLOYMENT_TYPE"
    echo ""
    
    check_dependencies
    create_logs_dir
    setup_env_files
    
    if [ "$DEPLOYMENT_TYPE" == "docker" ]; then
        deploy_docker
    elif [ "$DEPLOYMENT_TYPE" == "pm2" ]; then
        deploy_pm2
    else
        echo -e "${RED}Error: Invalid deployment type. Use 'docker' or 'pm2'${NC}"
        exit 1
    fi
    
    setup_nginx
    setup_ssl
    
    echo ""
    echo "================================================"
    echo "Deployment Complete!"
    echo "================================================"
    echo ""
    echo "Your app will be available at:"
    echo -e "${GREEN}https://rudrajadon.in/mpgroundwatermonitor${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Configure Nginx (see above)"
    echo "2. Setup SSL certificate (see above)"
    echo "3. Test the application"
    echo ""
}

# Run main function
main
