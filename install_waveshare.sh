#!/bin/bash

echo "Installing Waveshare e-Paper Library..."

# 1. 상위 폴더(홈 디렉토리 등)로 이동하여 다운로드
cd ..

# 2. Waveshare 공식 리포지토리 클론
if [ ! -d "e-Paper" ]; then
    echo "Cloning Waveshare e-Paper repository..."
    git clone https://github.com/waveshare/e-Paper
else
    echo "Updating existing e-Paper repository..."
    cd e-Paper
    git pull
    cd ..
fi

# 3. 라이브러리 폴더로 이동하여 설치
echo "Installing python library..."
cd e-Paper/RaspberryPi_JetsonNano/python

# (중요) 현재 활성화된 가상환경(.venv)의 python으로 설치합니다.
# sudo를 쓰면 시스템 전체에 깔려서 venv에서 못 찾을 수 있습니다.
python3 setup.py install

echo "========================================"
echo "Installation Complete!"
echo "Now you can run: python3 app.py"
echo "========================================"
