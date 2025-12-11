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

# 2. 확실하게 끄기 (자동실행 서비스 중단 + 포트 킬)
sudo systemctl stop photoframe.service
sudo systemctl disable photoframe.service
sudo fuser -k 8080/tcp

# 3. 서버 실행
python app.py
```
