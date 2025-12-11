# 📡 Raspberry Pi Deployment Guide

이 문서는 개발된 "Digital Photo Frame" 프로젝트를 **Raspberry Pi**에 배포하고 설정하는 과정을 안내합니다.

## 1. 하드웨어 준비 (Hardware Setup)

1.  **Raspberry Pi (Zero 2W, 3B, 4B 등)**
2.  **Waveshare 7.3inch e-Paper HAT (F)** (7-Color)
3.  **microSD 카드** (Raspberry Pi OS Lite 권장)

기기를 조립하고 HAT를 GPIO 핀에 올바르게 장착해주세요.

---

## 2. Raspberry Pi 초기 설정 (OS & SSH)

1.  **Raspberry Pi Imager**를 사용해 OS를 굽습니다.
    *   OS 선택: **Raspberry Pi OS Lite (64-bit)** 권장 (GUI 불필요)
    *   설정(톱니바퀴):
        *   **Hostname**: `photoframe` (원하는 이름)
        *   **SSH**: `Enable SSH` (비밀번호 인증)
        *   **Wi-Fi**: 사용할 와이파이 이름과 비밀번호 입력
2.  SD카드를 라즈베리파이에 넣고 전원을 켭니다.

---

## 3. SSH 접속

터미널(Mac/Windows)에서 라즈베리파이에 접속합니다.
```bash
# 설정한 hostname이 photoframe이고 유저명이 admin인 경우:
ssh admin@photoframe.local
```

---

## 4. 필수 시스템 패키지 설치

접속 후, 다음 명령어들을 순서대로 실행하여 시스템을 업데이트하고 필요한 패키지를 설치합니다.

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. 필수 라이브러리 설치 (Python, Git, SPI, GPIO 등)
sudo apt install -y python3-pip python3-venv git libopenjp2-7 libtiff5 libatlas-base-dev
```

### ⚙️ SPI 인터페이스 활성화 (E-Ink 필수)
```bash
sudo raspi-config
# 1. 'Interface Options' 선택
# 2. 'SPI' 선택 -> 'Yes' (Enable)
# 3. 'Finish' 후 재부팅 필요할 수 있음 (나중에 해도 됨)
```

---

## 5. 프로젝트 코드 다운로드 (Git Clone)

GitHub에 올린 코드를 받아옵니다.

```bash
# 홈 디렉토리로 이동
cd ~

# 레포지토리 복제 (본인 레포 주소 입력)
git clone https://github.com/chalky100024-alt/CSR_PROJECT.git

# 폴더 이동
cd CSR_PROJECT
```

---

## 6. 가상환경 및 Python 패키지 설치

```bash
# 1. 가상환경 생성 (.venv)
python3 -m venv .venv

# 2. 가상환경 활성화
source .venv/bin/activate

# 3. 필수 Python 라이브러리 설치
pip install -r requirements.txt

# 4. Waveshare E-Ink 드라이버 설치 (필수)
# RPi.GPIO와 spidev는 라즈베리파이에서만 설치 가능합니다.
pip install RPi.GPIO spidev
```

---

## 7. Waveshare 드라이버 확인 (중요)

`hardware.py`가 `waveshare_epd` 라이브러리를 참조합니다. 만약 프로젝트 폴더 내에 해당 라이브러리가 없다면 아래와 같이 Waveshare 공식 Repos를 받아 라이브러리를 복사해야 합니다.

*(이미 프로젝트 내 `lib` 폴더 등에 포함해서 커밋했다면 이 단계는 건너뛰세요. 만약 없다면 아래 수행)*

```bash
cd ~
git clone https://github.com/waveshare/e-Paper.git
# 필요한 드라이버 파일(epd7in3f.py 등)과 config 파일을 프로젝트 경로로 복사
# (이 부분은 개발 환경에서 미리 `lib` 폴더에 포함시켜두는 것이 가장 좋습니다)
```
*(참고: 우리 프로젝트에는 이미 `hardware.py`가 드라이버를 로드하도록 되어 있지만, 실제 `.py` 드라이버 파일이 누락되어있을 수 있습니다. 확인해 뵙시다.)*

---

## 8. 실행 및 테스트

```bash
# 프로젝트 폴더에서 (.venv 가 켜진 상태)
python3 app.py
```
*   에러가 없다면 `Running on http://0.0.0.0:8080` 메시지가 뜹니다.
*   PC나 폰 브라우저에서 `http://photoframe.local:8080` 접속 확인.
*   **[설정]** 메뉴에서 API 키 등을 입력하면 `config.json`이 생성됩니다.

---

## 9. 자동 실행 등록 (Systemd Service)

전원을 켰을 때 자동으로 실행되게 하려면 서비스 파일을 만듭니다.

1.  서비스 파일 작성:
```bash
sudo nano /etc/systemd/system/photoframe.service
```

2.  내용 붙여넣기 (경로/유저명 수정 주의):
```ini
[Unit]
Description=Digital Photo Frame Web Server
After=network.target

[Service]
User=admin
WorkingDirectory=/home/admin/CSR_PROJECT
ExecStart=/home/admin/CSR_PROJECT/.venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3.  서비스 등록 및 시작:
```bash
sudo systemctl daemon-reload
sudo systemctl enable photoframe.service
sudo systemctl start photoframe.service
```

이제 전원만 넣으면 자동으로 액자가 켜집니다! 🎉
