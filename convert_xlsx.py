import pandas as pd
import os

xlsx_file = "기상청41_단기예보 조회서비스_오픈API활용가이드_격자_위경도(2510).xlsx"
# Check if file exists with different normalization or just partial match if strict name fails
if not os.path.exists(xlsx_file):
    # Try to find it
    files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if files:
        xlsx_file = files[0]
        print(f"Found xlsx file: {xlsx_file}")

csv_file = "기상청41_단기예보 조회서비스_오픈API활용가이드_격자_위경도(2510).xlsx - 최종 업데이트 파일_20251027.csv"

try:
    df = pd.read_excel(xlsx_file)
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"Successfully converted {xlsx_file} to {csv_file}")
except Exception as e:
    print(f"Error converting file: {e}")
