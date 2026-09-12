#!/bin/bash

cd /Users/rudrajadon/Downloads/groundwater-app

echo "📦 Adding fixed files..."
git add frontend/pages/rainfall-analysis.tsx
git add frontend/lib/location-api.ts
git add frontend/lib/api.ts
git add frontend/tsconfig.json
git add frontend/.env.production

echo ""
echo "📝 Committing..."
git commit -m "Fix: TypeScript errors for Vercel deployment"

echo ""
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Done! Check Vercel for auto-deployment"
