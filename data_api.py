import requests
import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def get_fine_dust_data(api_key, station_name):
    if not api_key: return None
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
    params = {
        'serviceKey': api_key, 
        'returnType': 'json', 
        'numOfRows': '1', 
        'pageNo': '1',
        'stationName': station_name, 
        'dataTerm': 'DAILY', 
        'ver': '1.3'
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        items = res.json().get('response', {}).get('body', {}).get('items', [])
        if items:
            return {
                'pm10': int(items[0]['pm10Value']), 
                'pm25': int(items[0]['pm25Value']),
                'time': items[0]['dataTime']
            }
    except Exception as e:
        logger.error(f"Dust API Error: {e}")
        pass
    return None

def get_kma_base_time(api_type='ultrasrt'):
    now = datetime.now()
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

def get_weather_data(api_key, nx, ny):
    if not api_key: return None
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
            '_type': 'xml'
        }

        root = ET.fromstring(requests.get(url, params=params, timeout=10).text)
        for item in root.findall(".//item"):
            cat = item.find("category").text
            val = item.find("obsrValue").text
            if cat == 'T1H':
                try: weather_info['temp'] = float(val)
                except: weather_info['temp'] = 0.0
            elif cat == 'RN1':
                # '강수없음' or 'null' handling
                try: weather_info['current_rain_amount'] = float(val)
                except: weather_info['current_rain_amount'] = 0.0

        # 2. 초단기예보
        bd, bt = get_kma_base_time('ultrasrt_fcst')
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
        params['base_date'] = bd;
        params['base_time'] = bt;
        params['numOfRows'] = '60'

        root = ET.fromstring(requests.get(url, params=params, timeout=10).text)
        forecasts = {}
        for item in root.findall(".//item"):
            dt = item.find("fcstDate").text + item.find("fcstTime").text
            if dt not in forecasts: forecasts[dt] = {}
            forecasts[dt][item.find("category").text] = item.find("fcstValue").text

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
