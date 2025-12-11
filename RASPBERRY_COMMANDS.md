# 🚀 Rasberry Pi Update & Key Transfer Guide

**Target Device**: `pi@raspberrypi.local`

## 1. 🖥️ Mac에서 실행 (키 파일 전송)
방금 저장한 `config.json` (Google Key 포함)을 라즈베리파이로 보냅니다.
*터미널을 열고 프로젝트 폴더(`~/Desktop/CSR_PROJECT`)에서 실행하세요.*

```bash
# 설정 파일 전송 (비밀번호 입력 필요)
scp my_frame_web/config.json pi@raspberrypi.local:~/CSR_PROJECT/my_frame_web/
```

---

## 2. 🍓 Raspberry Pi에서 실행 (업데이트)
라즈베리파이에 접속해서 코드를 최신으로 받고 재시작합니다.

```bash
# 1. SSH 접속
ssh pi@raspberrypi.local

# --- (아래부터는 라즈베리파이 안에서 실행) ---

# 2. 프로젝트 폴더로 이동
cd ~/CSR_PROJECT

# 3. 최신 코드 받기
git pull origin main

# 4. (혹시 모르니) 라이브러리 업데이트
source .venv/bin/activate
pip install -r requirements.txt
pip install huggingface_hub

# 5. 서버 수동 실행 (개발용)
# (이미 실행 중인 게 있다면 Ctrl+C로 끄고 다시 실행)
python app.py
```
