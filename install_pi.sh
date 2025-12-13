#!/bin/bash
echo "🚀 Updating MyFrame Project..."

# 1. Update Code
git pull origin main

# 2. Python Backend Setup
echo "🐍 Installing Python Dependencies..."
# Ensure system deps for Pillow/Heif
# sudo apt-get install -y libopenjp2-7 libtiff5 libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk libharfbuzz-dev libfribidi-dev libxcb1-dev

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
pip install flask-cors pillow-heif h11==0.14.0 # Specific fix for some Pi versions

# 3. Frontend Setup
echo "⚛️ Building Frontend..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Installing Node 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

cd my_frame_frontend
npm install
npm run build 
# Build output goes to my_frame_frontend/dist

# 4. Move Build to Flask Static
echo "📂 Moving Build files..."
cd ..
# Cleanup old static
rm -rf my_frame_web/static/*
rm -rf my_frame_web/templates/index.html

# Copy new assets
# Vite builds assets into dist/assets and index.html
cp -r my_frame_frontend/dist/assets my_frame_web/static/
cp my_frame_frontend/dist/index.html my_frame_web/templates/

echo "✅ Update Complete!"
echo "👉 Run: source venv/bin/activate && python app.py"
