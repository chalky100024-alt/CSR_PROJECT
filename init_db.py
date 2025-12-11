import sqlite3
import csv
import os

# CSV 파일명 (사용자가 업로드한 파일명)
CSV_FILE = "기상청41_단기예보 조회서비스_오픈API활용가이드_격자_위경도(2510).xlsx - 최종 업데이트 파일_20251027.csv"
DB_FILE = "korea_zone.db"

def create_db():
    if not os.path.exists(CSV_FILE):
        print(f"❌ 오류: {CSV_FILE} 파일이 없습니다.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 테이블 생성 (동 이름 검색을 위해 인덱스 추가)
    c.execute('''CREATE TABLE IF NOT EXISTS locations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  si TEXT, gu TEXT, dong TEXT, 
                  nx INTEGER, ny INTEGER)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_dong ON locations (dong)')

    print("🔄 CSV 데이터를 DB로 변환 중... (잠시만 기다려주세요)")
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            rdr = csv.reader(f)
            # 헤더 3줄 건너뛰기 (기상청 파일 특성)
            for _ in range(3): 
                next(rdr, None)
                
            count = 0
            batch = []
            for row in rdr:
                if len(row) < 15: continue
                # 시/도, 시/군/구, 읍/면/동, 격자X, 격자Y
                si = row[2]
                gu = row[3]
                dong = row[4]
                nx = row[5]
                ny = row[6]
                
                if dong: # 동 이름이 있는 경우만 저장
                    batch.append((si, gu, dong, nx, ny))
                    count += 1
                
                if len(batch) > 1000:
                    c.executemany('INSERT INTO locations (si, gu, dong, nx, ny) VALUES (?,?,?,?,?)', batch)
                    batch = []
            
            if batch:
                c.executemany('INSERT INTO locations (si, gu, dong, nx, ny) VALUES (?,?,?,?,?)', batch)

        conn.commit()
        print(f"✅ DB 생성 완료! 총 {count}개 지역 저장됨.")
        
    except Exception as e:
        print(f"❌ 변환 중 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_db()
