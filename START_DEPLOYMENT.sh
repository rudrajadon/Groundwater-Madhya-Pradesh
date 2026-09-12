#!/bin/bash

# 🚀 Simple Deployment Script
# This will help you deploy MP Groundwater Monitor in 10 minutes

echo "=========================================="
echo "🚀 MP Groundwater Monitor Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}✓ Git is already initialized${NC}"
echo ""

echo "=========================================="
echo "📋 Deployment Checklist"
echo "=========================================="
echo ""
echo "PART 1: Deploy Backend to Render (5 min)"
echo "  1. Go to: https://render.com"
echo "  2. Sign up and create new Web Service"
echo "  3. Connect this repository"
echo "  4. Use these settings:"
echo "     - Root Directory: backend"
echo "     - Build: pip install -r requirements.txt"
echo "     - Start: uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo "     - Plan: Free"
echo "  5. Copy your backend URL"
echo ""

echo "PART 2: Deploy Frontend to Vercel (5 min)"
echo "  1. First, update frontend/.env.production with backend URL"
echo "  2. Push code to GitHub"
echo "  3. Go to: https://vercel.com"
echo "  4. Import your GitHub repository"
echo "  5. Set Root Directory: frontend"
echo "  6. Add domain: rudrajadon.in"
echo ""

echo "=========================================="
echo "🎯 Let's Start!"
echo "=========================================="
echo ""

# Check if GitHub remote exists
if git remote -v | grep -q origin; then
    echo -e "${GREEN}✓ GitHub remote already configured${NC}"
    echo "  Remote URL: $(git remote get-url origin)"
else
    echo -e "${YELLOW}⚠ No GitHub remote found${NC}"
    echo ""
    echo "To add GitHub remote:"
    echo "  1. Create repo on GitHub: https://github.com/new"
    echo "  2. Run: git remote add origin YOUR_REPO_URL"
fi

echo ""
echo "=========================================="
echo "📝 Next Steps"
echo "=========================================="
echo ""
echo "Read the complete guide: SIMPLE_DEPLOY.md"
echo ""
echo "Quick commands:"
echo "  1. git add ."
echo "  2. git commit -m \"Ready for deployment\""
echo "  3. git push origin main"
echo ""
echo "Then follow SIMPLE_DEPLOY.md for Render and Vercel setup!"
echo ""
echo "=========================================="
echo "🎉 Your app will be live at:"
echo "   https://rudrajadon.in/mpgroundwatermonitor"
echo "=========================================="
