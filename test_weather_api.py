
import requests
import datetime
from datetime import timedelta
import xml.etree.ElementTree as ET
import json

API_KEY = "F3I3IeSUH4yLzn6o45Qwob4eGGydLmGax83sAzxr3FH2h82xRoHO5afglEMsRuQ6enj4qJaF2UCQo89cSWHuKg=="
NX = 61
NY = 115

def get_kma_base_time(api_type='ultrasrt'):
    now = datetime.datetime.now()
    base_date = now.strftime('%Y%m%d')
    if now.minute < 40:
        if now.hour == 0:
            base_time = "2330"
            base_date = (now - timedelta(days=1)).strftime('%Y%m%d')
        else:
            base_time = (now - timedelta(hours=1)).strftime('%H') + "30"
    else:
        base_time = now.strftime('%H') + "30"
    return base_date, base_time

def test_api():
    bd, bt = get_kma_base_time('ultrasrt')
    print(f"Calculated Base Time: Date={bd}, Time={bt}")
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        'serviceKey': API_KEY, 
        'numOfRows': '10', 
        'pageNo': '1',
        'base_date': bd, 
        'base_time': bt, 
        'nx': NX, 
        'ny': NY, 
        '_type': 'xml'
    }
    
    print(f"Requesting URL: {url}")
    print(f"Params: {params}")
    
    try:
        res = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {res.status_code}")
        print(f"Response Body (First 500 chars): {res.text[:500]}")
        
        root = ET.fromstring(res.text)
        items = root.findall(".//item")
        print(f"Found {len(items)} items.")
        
        weather_info = {}
        for item in items:
            cat = item.find("category").text
            val = item.find("obsrValue").text
            print(f"  Category: {cat}, Value: {val}")
            if cat == 'T1H':
                weather_info['temp'] = float(val)
        
        print("\nParsed Info:")
        print(weather_info)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
