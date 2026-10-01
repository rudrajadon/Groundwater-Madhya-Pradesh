#!/bin/bash

cd /Users/rudrajadon/Downloads/groundwater-app

echo "🔧 Fixing 404 error by removing basePath temporarily..."

git add frontend/next.config.js

git commit -m "Fix: Remove basePath for Vercel root deployment"

git push origin main

echo ""
echo "✅ Done! Vercel will redeploy in 1-2 minutes"
echo ""
echo "After redeploy, access your app at:"
echo "https://YOUR-VERCEL-URL/ (root path)"
echo ""
echo "Once we connect your domain, we'll add basePath back for:"
echo "https://rudrajadon.in/mpgroundwatermonitor"
