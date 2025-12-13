# 🛠️ Web App Debugging Guide (Frontend & Backend)

이 프로젝트는 **두 개의 서버**가 동시에 돌아가는 구조입니다.
1. **Backend (Flask)**: 데이터 처리, AI 생성, 하드웨어 제어 (Port 8080)
2. **Frontend (React)**: 사용자 화면 (Port 5173)

문제가 생겼을 때 어디를 봐야 하는지 정리해 드립니다.

---

## 1. 🖥️ Frontend 디버깅 (화면이 이상할 때)
**도구**: 크롬(Chrome) 브라우저 개발자 도구 (**F12** 키)

### A. Console (콘솔) 탭
빨간색 에러 메시지를 확인합니다.
- **`Uncaught TypeError`**: 자바스크립트 코드 오류입니다 (오타, null 참조 등).
- **`CORS Policy Error`**: 프론트엔드(5173)가 백엔드(8080)로 요청을 보낼 권한이 없을 때 뜹니다. (`app.py`의 `flask-cors` 설정 확인 필요)
- **`404 Not Found`**: 파일을 못 찾거나 API 주소가 틀렸을 때.

### B. Network (네트워크) 탭 (★가장 중요★)
API 요청이 제대로 가고 있는지 확인합니다.
1. Network 탭을 엽니다.
2. 문제가 되는 버튼(예: "AI 생성하기")을 누릅니다.
3. 목록에 생기는 요청(Name)을 클릭합니다.
    - **Header**: 요청 주소가 맞는지 확인 (예: `http://localhost:5173/api/generate_ai`)
    - **Payload**: 내가 보낸 데이터(Prompt 등)가 맞는지 확인.
    - **Response**: 서버가 보내준 응답 확인.
        - 만약 응답이 JSON이 아니라 `<DOCTYPE html...`이 온다면? **Proxy 설정 오류**입니다. (백엔드가 아니라 프론트엔드 HTML을 받아온 것)

---

## 2. ⚙️ Backend 디버깅 (기능이 안 될 때)
**도구**: 터미널 (Terminal)

### A. Flask 로그 확인
`python app.py`를 실행한 터미널을 봅니다.
- 프론트에서 요청을 보내면 로그가 한 줄씩 올라옵니다.
  ```text
  127.0.0.1 - - [Time] "POST /api/generate_ai HTTP/1.1" 200 -
  ```
- **200**: 성공
- **500**: 서버 내부 오류 (터미널에 파이썬 에러 메시지(Traceback)가 뜹니다. 이걸 봐야 원인을 압니다.)
- **404**: 없는 주소 요청

### B. print() 디버깅
코드가 의심스러울 때 `app.py` 중간중간에 `print()`를 넣으세요.
```python
@app.route('/api/test')
def test():
    print(f"--> 요청 받음! 데이터: {request.json}") # 터미널에 출력됨
    ...
```
Flask는 `debug=True` 모드라 코드 수정 후 저장하면 자동으로 재시작됩니다.

---

## 3. 🚨 자주 발생하는 문제 및 해결

### 상황 1: "API Error" 알림이 뜨고 아무것도 안 돼요.
1. **Network 탭**을 봅니다. 빨간색 요청이 있는지 확인합니다.
2. 빨간색 요청을 클릭 -> **Response** 탭을 봅니다. 서버가 보낸 에러 메시지가 있을 겁니다.
3. **백엔드 터미널**을 봅니다. 파이썬 오류(`KeyError`, `ValueError` 등)가 떴는지 확인합니다.

### 상황 2: 이미지가 안 보여요 (깨진 아이콘).
1. 이미지 요소 우클릭 -> **"새 탭에서 이미지 열기"**.
2. 주소창의 URL을 확인합니다.
    - `http://localhost:5173/uploads/photo.jpg` -> 프론트엔드 서버로 요청함 (Proxy가 처리해줘야 함).
3. `uploads` 폴더에 진짜 그 파일이 있는지 확인합니다.

### 상황 3: 프론트엔드 코드를 고쳤는데 안 바뀌어요.
- 브라우저가 예전 코드를 기억하고 있을 수 있습니다.
- **강력 새로고침**: `Cmd + Shift + R` (맥) / `Ctrl + Shift + R` (윈도우)

### 상황 4: `npx` / `npm` 에러
- `node_modules`가 꼬였을 수 있습니다.
- 해결: `rm -rf node_modules package-lock.json && npm install`
