import requests
import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
try:
    from utils.logger import log_debug
except ImportError:
    log_debug = lambda msg, level='info': None # Fallback

import time

logger = logging.getLogger(__name__)

def fetch_with_retry(url, params, retries=3, timeout=30, label="API"):
    """
    Robust fetcher with retries and timeout.
    """
    for i in range(retries):
        try:
            log_debug(f"{label} Req (Attempt {i+1}): {url}")
            t0 = datetime.now()
            res = requests.get(url, params=params, timeout=timeout)
            dt = (datetime.now() - t0).total_seconds()
            log_debug(f"{label} Res: {res.status_code} ({dt:.2f}s)")
            
            if res.status_code == 200:
                return res
            else:
                 logger.warning(f"{label} returned status {res.status_code}. Retrying...")
                 
        except Exception as e:
            logger.warning(f"{label} Attempt {i+1} Failed: {e}")
            log_debug(f"{label} Error: {e}", level='warning')
        
        if i < retries - 1:
            time.sleep(2) # Wait 2s before retry
            
    # Final Attempt failed
    logger.error(f"{label} Failed after {retries} attempts.")
    return None

def get_fine_dust_data(api_key, station_name):
    if not api_key: return None
    
    # ... (Key Handling omitted, assume context fits)
    # Re-insert key handling because replace_file_content needs context match
    # Wait, I cannot skip context. I need to be precise.
    # I will replace the imports + top of function to inject helper.
    
    # [Robust Key Handling]
    if '%' in api_key:
        try:
            from urllib.parse import unquote
            api_key = unquote(api_key)
        except: pass

    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
    params = {
        'serviceKey': api_key, 'returnType': 'json', 'numOfRows': '1', 
        'pageNo': '1', 'stationName': station_name, 'dataTerm': 'DAILY', 'ver': '1.3'
    }

    try:
        res = fetch_with_retry(url, params, label="Dust API")
        if not res: return None
        data = res.json()
        logger.info(f"Dust API Params: {params}") 
 
        # logger.info(f"Dust API Response: {data}") # Uncomment if needed, can be noisy

        items = data.get('response', {}).get('body', {}).get('items', [])
        if items:
            return {
                'pm10': int(items[0]['pm10Value']), 
                'pm25': int(items[0]['pm25Value']),
                'time': items[0]['dataTime']
            }
        else:
             logger.warning("Dust API: No items found in response.")
             logger.warning(f"RAW RES: {res.text[:500]}") # Log first 500 chars
             
    except Exception as e:
        logger.error(f"Dust API Error: {e}")
        try: logger.error(f"RAW RES (Error): {res.text[:1000]}")
        except: pass
        
    return None

def get_kma_base_time(api_type='ultrasrt'):
    now = datetime.now()
    if api_type == 'ultrasrt': # 초단기실황 (매시 40분 이후)
        if now.minute < 45: # 안전하게 45분 기준
            now = now - timedelta(hours=1)
        base_time = now.strftime('%H') + "00"
        base_date = now.strftime('%Y%m%d')
    else: # 초단기예보 (매시 45분 마다 생성)
        if now.minute < 45:
            now = now - timedelta(hours=1)
        base_time = now.strftime('%H') + "30"
        base_date = now.strftime('%Y%m%d')
        
    return base_date, base_time

def get_weather_data(api_key, nx, ny):
    if not api_key: return None
    # Decode API Key if it's URL encoded (Common mistake)
    if '%' in api_key:
        try:
            from urllib.parse import unquote
            api_key = unquote(api_key)
        except: pass
        
    weather_info = {}
    try:
        # 1. 초단기실황
        bd, bt = get_kma_base_time('ultrasrt')
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        params = {
            'serviceKey': api_key, 
            'numOfRows': '10', 
            'pageNo': '1',
            'base_date': bd, 
            'base_time': bt, 
            'nx': nx, 
            'ny': ny, 
            'dataType': 'JSON' # Changed to JSON for easier debug
        }
        
        # Requests automatically encodes params, but serviceKey is tricky.
        # We must append serviceKey manually if normal params fail.
        # But requests usually handles it. try manual string construction if fails.
        
        logger.info(f"🌤️ Weather API Request: {url}")
        logger.info(f"🔑 Key used: {api_key[:10]}... (Contains %: {'%' in api_key})")
        
        res = fetch_with_retry(url, params, label="Weather(1)")
        
        logger.info(f"📡 Final URL: {res.url if res else 'None'}") 
        
        try:
            if not res: raise Exception("Weather(1) Fetch Failed")
            data = res.json()
            items = data['response']['body']['items']['item']
        except: 
            # JSON Fail -> Try XML Fallback logic or just Log
            logger.error(f"Weather JSON Parse Fail. Status: {res.status_code}")
            logger.error(f"Raw Response: {res.text[:500]}") # Print first 500 chars
            items = []

        for item in items:
            cat = item['category']
            val = item['obsrValue']
            if cat == 'T1H':
                try: weather_info['temp'] = float(val)
                except: weather_info['temp'] = 0.0
            elif cat == 'RN1':
                try: weather_info['current_rain_amount'] = float(val)
                except: weather_info['current_rain_amount'] = 0.0

        # 2. 초단기예보
        bd, bt = get_kma_base_time('ultrasrt_fcst')
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
        params['base_date'] = bd
        params['base_time'] = bt
        params['numOfRows'] = '60'
        
        res = fetch_with_retry(url, params, label="Weather(2)")
        
        try:
            if not res: raise Exception("Weather(2) Fetch Failed")
            data = res.json()
            items = data['response']['body']['items']['item']
        except: items = []
        
        forecasts = {}
        for item in items:
            dt = item['fcstDate'] + item['fcstTime']
            if dt not in forecasts: forecasts[dt] = {}
            forecasts[dt][item['category']] = item['fcstValue']

        now = datetime.now()
        closest_time = min(
            [t for t in forecasts.keys() if datetime.strptime(t, '%Y%m%d%H%M') >= now - timedelta(minutes=30)],
            key=lambda x: abs(datetime.strptime(x, '%Y%m%d%H%M') - now), default=None)

        if closest_time:
            sky = int(forecasts[closest_time].get('SKY', '1'))
            pty = int(forecasts[closest_time].get('PTY', '0'))
            weather_info['weather_main_code'] = pty
            if pty == 0:
                weather_info['weather_description'] = ['맑음', '맑음', '구름 많음', '흐림'][sky - 1] if sky <= 4 else '흐림'
            else:
                weather_info['weather_description'] = ['', '비', '비 또는 눈', '눈', '소나기'][pty]
        else:
             # Fallback if no forecast
             weather_info['weather_description'] = '정보없음'

        # 6시간 강수 예보
        max_rain = None
        for t in sorted(forecasts.keys()):
            ft = datetime.strptime(t, '%Y%m%d%H%M')
            if now <= ft <= now + timedelta(hours=6):
                pty = int(forecasts[t].get('PTY', '0'))
                try:
                    rn1_val = forecasts[t].get('RN1', '0')
                    if rn1_val in ['강수없음', 'null', '-']: rn1 = 0.0
                    else: rn1 = float(rn1_val)
                except: rn1 = 0.0
                if pty > 0 and rn1 > 0:
                    if not max_rain or rn1 > max_rain['amount']:
                        max_rain = {'amount': rn1, 'start_time': ft.strftime('%H:%M'),
                                    'end_time': (ft + timedelta(hours=1)).strftime('%H:%M'), 'type_code': pty}
        weather_info['rain_forecast'] = max_rain
        
        # Merge Temp if present in forecast but missed in live (fallback)
        if 'temp' not in weather_info and closest_time:
             if 'T1H' in forecasts[closest_time]:
                 weather_info['temp'] = float(forecasts[closest_time]['T1H'])
                 
        return weather_info
    except Exception as e:
        logger.error(f"Weather API Error: {e}")
        # Return partial info if available
        if weather_info: return weather_info
        return None
