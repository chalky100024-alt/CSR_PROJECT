#!/bin/bash
echo "🚀 Building Frontend..."
cd my_frame_frontend
npm install
npm run build

echo "📂 Deploying to Flask..."
# Clear old static files (be careful not to delete uploads if they were there, but uploads are in sibling dir)
# static folder usually contains only build artifacts in this setup
rm -rf ../my_frame_web/static/*
# Copy new build
cp -r dist/* ../my_frame_web/static/

# Move index.html to templates
mv ../my_frame_web/static/index.html ../my_frame_web/templates/index.html

echo "✅ Build & Deploy Complete!"
