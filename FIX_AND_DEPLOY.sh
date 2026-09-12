#!/bin/bash

cd /Users/rudrajadon/Downloads/groundwater-app

echo "🔍 Checking if location-api.ts is tracked..."
git ls-files frontend/lib/location-api.ts

echo ""
echo "📦 Adding all necessary files..."
git add -f frontend/lib/location-api.ts
git add -f frontend/lib/api.ts
git add frontend/tsconfig.json
git add frontend/.env.production

echo ""
echo "📝 Committing..."
git commit -m "Fix: Ensure all lib files are committed for Vercel build"

echo ""
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Done! Vercel should auto-redeploy now."
echo ""
echo "If build still fails, go to Vercel dashboard and click 'Redeploy'"
