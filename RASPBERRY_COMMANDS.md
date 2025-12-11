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

# 5. 서비스 재시작 (화면이 깜빡이며 갱신됩니다)
sudo systemctl restart photoframe.service

# (선택) 잘 실행되는지 로그 확인하기 (나갈 땐 Ctrl+C)
sudo journalctl -u photoframe.service -f
```
