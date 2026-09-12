#!/bin/bash

cd /Users/rudrajadon/Downloads/groundwater-app

echo "🔧 Adding files..."
git add frontend/.env.production
git add frontend/tsconfig.json

echo "📝 Committing..."
git commit -m "Fix: Update tsconfig moduleResolution for Vercel deployment"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Done! Now trigger redeploy in Vercel dashboard"
