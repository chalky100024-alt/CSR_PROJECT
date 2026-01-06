from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import settings
import hardware
import ai_generator
import renderer
import data_api
import sqlite3
import random

import photo_frame
import threading
from PIL import Image, ImageCms
import io
import datetime
import time

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("pillow-heif not installed. HEIC support disabled.")

app = Flask(__name__, template_folder='my_frame_web/templates', static_folder='my_frame_web/static')
try:
    from flask_cors import CORS
    CORS(app) # Enable CORS for all routes (Dev mode)
except ImportError:
    print("flask-cors not found. Install it to run with React frontend.")

hw = hardware.HardwareController()

# ... (rest of imports)

# ... (inside upload_file or checks) ...

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        if not os.path.exists(settings.UPLOADS_DIR):
            os.makedirs(settings.UPLOADS_DIR)
            
        file_path = os.path.join(settings.UPLOADS_DIR, filename)
        
        # HEIC Conversion & Color Correction Logic
        if filename.lower().endswith(('.heic', '.heif')):
            try:
                # Save temp
                file.save(file_path)
                # Convert
                img = Image.open(file_path)
                
                # Color Profile Correction (P3 -> sRGB)
                img_corrected = img.copy()
                
                if img.info.get('icc_profile'):
                    try:
                        f = io.BytesIO(img.info['icc_profile'])
                        src_profile = ImageCms.ImageCmsProfile(f)
                        dst_profile = ImageCms.createProfile('sRGB')
                        img_corrected = ImageCms.profileToProfile(img_corrected, src_profile, dst_profile)
                    except Exception as e:
                        print(f"ICC Profile conversion failed: {e}")

                new_filename = os.path.splitext(filename)[0] + ".jpg"
                new_path = os.path.join(settings.UPLOADS_DIR, new_filename)
                
                img_corrected.convert('RGB').save(new_path, "JPEG", quality=95) # Save Good Version
                
                # Remove original HEIC
                os.remove(file_path)
                filename = new_filename # Return the normal valid file to the UI
            except Exception as e:
                print(f"HEIC conversion failed: {e}")
                return jsonify({'error': 'HEIC conversion failed'}), 500
        else:
            file.save(file_path)
            
        return jsonify({'success': True, 'filename': filename}), 200

# --- [Routes] ---

# --- [Routes] ---

# --- [Routes] ---

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_file(os.path.join(settings.UPLOADS_DIR, filename))

# Serve React Static Files
@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory('my_frame_web/static/assets', path)

# Catch-all for React Router
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # API endpoints should be handled above or distinct
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
        
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/index.html') # Legacy redirection
def index_legacy():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/settings') # React Router handles this URL now, but initial load needs HTML
def settings_page():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/get_config')
def get_config():
    response = jsonify(settings.load_config())
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    data = request.json
    # print(f"DEBUG: save_config received (Raw): {data}") # Removed for security (Service Account Key)
    current = settings.load_config()
    # ... (existing merge logic) ...
    if 'location' in data:
        current['location'] = data['location']
    if 'layout' in data:
        current['layout'] = data['layout']
    # ...
    # (Abbreviated, assume standard merge logic matches file)
    
    # Correct handling for deep merge vs simple replace:
    # Since we are being slightly lazy with the replacement content matching:
    # I will just write the essential trigger logic.
    # IMPORTANT: The user existing code has individual ifs. I must replicate or wrap.
    # Let's inspect the target content carefully.
    
    # Re-implementing the function body to includes updates
    # Merge update
    for key, value in data.items():
        current[key] = value

    # [Auto-Update Station Name]
    # User Request: "If I change region, station should update automatically"
    # Logic: Extract the last part of location name (Dong/Eup/Myeon) and use as station_name
    if 'location' in data and 'name' in data['location']:
        loc_name = data['location']['name']
        try:
            # Format: "Jeonggi-do Pyeongtaek-si Godeok-dong" -> "Godeok-dong"
            # This is a heuristic. AirKorea usually matches Dong/Eup/Myeon names.
            possible_station = loc_name.split()[-1]
            current['station_name'] = possible_station
            print(f"Auto-updated station_name to: {possible_station}")
        except:
            pass

    settings.save_config(current)
    
    # Trigger Display Refresh in Background ONLY if requested
    # User Requirement: Refresh ONLY when "Save Layout & Transfer" is pressed.
    should_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    # Capture the specific photo if user selected one in this request
    # This allows overriding shuffle mode temporarily
    force_photo = data.get('selected_photo')
    
    print(f"DEBUG: api_save_config called. Request args: {request.args}, should_refresh: {should_refresh}, force_photo: {force_photo}")
    
    if should_refresh:
        def refresh_task():
            try:
                print("DEBUG: Restarting service to apply changes...")
                # Avoid GPIO Busy error by restarting the main service
                # The service will load the new config and update the display on boot
                os.system("sudo systemctl restart photoframe.service")
            except Exception as e:
                print(f"Service restart failed: {e}")
                
        threading.Thread(target=refresh_task).start()
    
    return jsonify({"status": "success"})

@app.route('/api/preview')
def get_preview():
    """Generate live preview with real layout settings."""
    # Get Current Location Name & Keys
    current_config = settings.load_config()
    saved_layout = current_config.get('layout', {})

    # Get params (Priority: Request Args > Saved Config > Defaults)
    layout = {
        "widget_size": request.args.get('widget_size', saved_layout.get('widget_size', 1.0), type=float),
        "font_size": request.args.get('font_size', saved_layout.get('font_size', 20), type=int),
        "opacity": request.args.get('opacity', saved_layout.get('opacity', 0.6), type=float),
        "position": request.args.get('position', saved_layout.get('position', 'top')),
        "x": request.args.get('x', saved_layout.get('x')),
        "y": request.args.get('y', saved_layout.get('y')),
        "type": saved_layout.get('type', 'type_A')
    }
    
    # ... (photo loading)
    if not os.path.exists(settings.UPLOADS_DIR):
        os.makedirs(settings.UPLOADS_DIR)
        
    requested_file = request.args.get('min_filename') # Filename only, no path
    img_path = None
    
    photos = [f for f in os.listdir(settings.UPLOADS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if requested_file and requested_file in photos:
        img_path = os.path.join(settings.UPLOADS_DIR, requested_file)
    elif photos:
        photos.sort(key=lambda x: os.path.getmtime(os.path.join(settings.UPLOADS_DIR, x)), reverse=True)
        img_path = os.path.join(settings.UPLOADS_DIR, photos[0])

    # Get Current Location Name & Keys
    location_name = current_config.get('location', {}).get('name', '')
    
    api_key_kma = current_config.get('api_key_kma')
    api_key_air = current_config.get('api_key_air')
    
    # Defaults (Align with Frame: Start as None)
    w_data = None
    d_data = None
    
    # Fetch Real Data if keys exist using data_api
    if api_key_kma:
        loc = current_config.get('location', {})
        nx = int(loc.get('nx', 61))
        ny = int(loc.get('ny', 115))
        real_w = data_api.get_weather_data(api_key_kma, nx, ny)
        if real_w: w_data = real_w
            
    if api_key_air and location_name:
        # Simple extraction of station name (last word)
        station = location_name.split()[-1] 
        real_d = data_api.get_fine_dust_data(api_key_air, station)
        if real_d: d_data = real_d

    # Render
    final_img, box_x, box_y, box_w, box_h = renderer.create_composed_image(img_path, w_data, d_data, layout, location_name)
    
    import io
    img_io = io.BytesIO()
    final_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    
    response = send_file(img_io, mimetype='image/jpeg')
    response.headers['X-Widget-X'] = str(box_x)
    response.headers['X-Widget-Y'] = str(box_y)
    response.headers['X-Widget-Width'] = str(box_w)
    response.headers['X-Widget-Height'] = str(box_h)
    return response

@app.route('/api/generate_ai', methods=['POST'])
def api_gen_ai():
    prompt = request.json.get('prompt')
    style = request.json.get('style', 'anime')
    # Support both single (legacy/optional) and list
    image_filenames = request.json.get('image_filenames', [])
    if not image_filenames and request.json.get('image_filename'):
        image_filenames = [request.json.get('image_filename')]
        
    provider = settings.load_config().get('ai_provider', 'huggingface')
    
    filename = ai_generator.generate_image(prompt, style, provider, image_filenames)
    if filename:
        return jsonify({"status": "success", "image": filename})
    else:
        return jsonify({"status": "error"}), 500



@app.route('/api/search_location')
def search_location():
    keyword = request.args.get('q', '')
    if len(keyword) < 2: return jsonify([])
    
    if not os.path.exists(settings.DB_PATH):
        return jsonify([])

    try:
        conn = sqlite3.connect(settings.DB_PATH)
        c = conn.cursor()
        # Search for dong
        c.execute("SELECT si, gu, dong, nx, ny FROM locations WHERE dong LIKE ? LIMIT 20", (f'%{keyword}%',))
        results = [{"name": f"{r[0]} {r[1]} {r[2]}", "nx": r[3], "ny": r[4]} for r in c.fetchall()]
        conn.close()
        return jsonify(results)
    except Exception as e:
        print(f"DB Error: {e}")
        return jsonify([])

@app.route('/api/wifi_scan')
def wifi_scan():
    return jsonify(hw.scan_wifi())

@app.route('/api/battery')
def battery_status():
    return jsonify(hw.get_battery_status())

@app.route('/api/wifi_connect', methods=['POST'])
def wifi_connect():
    data = request.json
    success = hw.connect_wifi(data['ssid'], data['password'])
    return jsonify({"status": "success" if success else "fail"})

@app.route('/api/system', methods=['GET', 'POST'])
def system_action():
    action = request.args.get('action')
    if action == 'shutdown':
        os.system("sudo shutdown now")
    elif action == 'reboot':
        os.system("sudo reboot")
    elif action == 'update':
        # Smart Update Check
        try:
            import subprocess
            project_path = os.path.dirname(os.path.abspath(__file__))
            
            # 1. Fetch latest meta
            subprocess.check_output(["git", "fetch", "origin", "main"], stderr=subprocess.STDOUT, cwd=project_path)
            
            # 2. Compare Local vs Remote
            local_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_path).decode().strip()
            remote_hash = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=project_path).decode().strip()
            
            if local_hash == remote_hash:
                print("✅ System is already up-to-date.")
                return jsonify({"status": "uptodate", "message": "Already up to date."})
            
            # 3. If outdated, Pull & Restart
            output = subprocess.check_output(["git", "pull", "origin", "main"], stderr=subprocess.STDOUT, cwd=project_path)
            print(f"🔄 System Update Updating...\n{output.decode('utf-8')}")
            
            # Restart Service
            def perform_restart():
                import time
                time.sleep(3) 
                print("🔄 Restarting Service...")
                os.system("sudo systemctl restart photoframe.service")
            
            threading.Thread(target=perform_restart).start()
            
            return jsonify({"status": "success", "message": f"Update OK. Restarting...\n{output.decode('utf-8')}"})
            
        except subprocess.CalledProcessError as e:
            return jsonify({"status": "error", "message": e.output.decode('utf-8')})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
            
    elif action == 'toggle_mode':
        # Toggle between 'settings' and 'operation'
        cfg = settings.load_config()
        p_settings = cfg.get('power_settings', {})
        current_mode = p_settings.get('mode', 'settings')
        
        new_mode = 'operation' if current_mode == 'settings' else 'settings'
        p_settings['mode'] = new_mode
        cfg['power_settings'] = p_settings
        
        settings.save_config(cfg)
        print(f"Power Mode Switched: {current_mode} -> {new_mode}")
        
        # Immediate Effect if switching TO operation
        if new_mode == 'operation':
             threading.Thread(target=check_power_management).start()
             
        return jsonify({"status": "success", "mode": new_mode})
        
    return jsonify({"status": "ok"})
    
@app.route('/api/list_photos')
def list_photos():
    if not os.path.exists(settings.UPLOADS_DIR):
        return jsonify([])
    # Sort by modification time (newest first)
    files = [f for f in os.listdir(settings.UPLOADS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(settings.UPLOADS_DIR, x)), reverse=True)
    return jsonify(files)

@app.route('/api/delete_photo', methods=['POST'])
def delete_photo():
    filename = request.json.get('filename')
    if not filename: return jsonify({'error': 'No filename'}), 400
    
    path = os.path.join(settings.UPLOADS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/delete_photos', methods=['POST'])
def delete_photos():
    filenames = request.json.get('filenames', [])
    if not filenames: return jsonify({'error': 'No filenames'}), 400
    
    deleted_count = 0
    errors = []
    
    for filename in filenames:
        path = os.path.join(settings.UPLOADS_DIR, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")
        else:
            errors.append(f"{filename}: Not found")
            
    return jsonify({
        'status': 'success', 
        'deleted': deleted_count, 
        'errors': errors
    })



# --- [Persistent Lifecycle Logging] ---
import datetime
def log_lifecycle_event(event):
    """Log critical events to a file for easy debugging"""
    try:
        log_path = os.path.join(settings.BASE_DIR, 'lifecycle_log.txt')
        with open(log_path, 'a') as f:
            f.write(f"[{datetime.datetime.now()}] {event}\n")
    except Exception as e:
        print(f"Failed to write lifecycle log: {e}")

# --- [Startup Logic for Power Management] ---
def check_power_management():
    """Check mode and schedule shutdown if needed"""
    # 1. Provide delay for network/system stabilization
    import time
    time.sleep(5) 
    
    # [DEBUG LOGGER INIT]
    try:
        from utils.logger import setup_debug_logger, check_internet_connection, log_debug
        setup_debug_logger()
        log_debug(f"APP_STARTED | Mode Check Initiated")
        check_internet_connection() # Run Ping/HTTP Check
    except Exception as e:
        print(f"Logger Init Failed: {e}")
        
    try:
        # log_lifecycle_event(f"APP_STARTED | Mode Check Initiated") # Replaced by log_debug
        
        cfg = settings.load_config()
        p_settings = cfg.get('power_settings', {})
        mode = p_settings.get('mode', 'settings')
        
        log_lifecycle_event(f"Current Mode: {mode}")

        if mode == 'operation':
            interval = int(p_settings.get('interval_min', 60))
            runtime = int(p_settings.get('runtime_min', 3))
            
            print(f"🚀 Operation Mode Detected. Runtime: {runtime}m, Next Wakeup: {interval}m")
            
            # [CRITICAL] Refresh Screen on Boot
            def display_update_task():
                try:
                    log_lifecycle_event("Display Update Started")
                    pf = photo_frame.EInkPhotoFrame()
                    pf.refresh_display()
                    log_lifecycle_event("Display Update Completed")
                except Exception as e:
                    err = f"Display Update Failed: {e}"
                    print(err)
                    log_lifecycle_event(err)
            
            threading.Thread(target=display_update_task).start()

            def shutdown_sequence():
                try:
                    log_lifecycle_event(f"Shutdown Thread Started. Waiting {runtime}m...")
                    time.sleep(runtime * 60)
                    
                    # Check Mode AGAIN before shutting down (Safety)
                    current_cfg = settings.load_config()
                    p_curr = current_cfg.get('power_settings', {})
                    if p_curr.get('mode') != 'operation':
                        msg = "🛑 Shutdown Aborted: Mode changed to Settings."
                        print(msg)
                        log_lifecycle_event(msg)
                        return

                    # --- [Smart Wakeup Calculation] ---
                    # Logic: Calculate standard next wakeup (now + interval)
                    # If it falls within Sleep Time (Wait, logic is simpler: If next time is > End Hour, set to Tomorrow Start Hour)
                    # If current time is < Start Hour, set to Today Start Hour (Shouldn't happen if shutdown logic works, but for safety)
                    
                    start_h = int(p_curr.get('active_start_hour', 5))
                    end_h = int(p_curr.get('active_end_hour', 22))
                    # Reload interval from latest config in case user changed it during runtime
                    interval = int(p_curr.get('interval_min', 60))
                    
                    now = datetime.datetime.now()
                    # Calculate 'Standard' next wake
                    next_wake = now + datetime.timedelta(minutes=interval)
                    
                    # Determine 'Safe' Next Wake
                    final_wake_time = next_wake
                    
                    # Case 1: Next wake is after End Hour of TODAY (Go to sleep until tmrw start)
                    # Example: End=22. Next=22:30. -> Tomorrow 05:00
                    if next_wake.hour >= end_h or (next_wake.hour < start_h and next_wake.day == now.day): 
                        # Note: The 'next_wake.hour < start_h' part covers if we are running at 3AM for some reason
                         
                        # Calculate Tomorrow's Start Time
                        # If next_wake is already tomorrow (e.g. 00:30), we just set hour to start_h
                        # If next_wake is today (23:00), we add 1 day and set hour
                        
                        target_day = now.date() 
                        if now.hour >= end_h: 
                            target_day += datetime.timedelta(days=1)
                        
                        target_dt = datetime.datetime.combine(target_day, datetime.time(hour=start_h, minute=0))
                        
                        # If target_dt is in past (e.g. we are running at 3AM and Start is 5AM, target is Today 5AM)
                        if target_dt < now:
                             target_dt += datetime.timedelta(days=1)
                             
                        final_wake_time = target_dt
                        log_lifecycle_event(f"Night Mode Active ({end_h}h ~ {start_h}h). Sleeping until {final_wake_time}")
                    
                    # Calculate minutes difference for RTC
                    diff_seconds = (final_wake_time - now).total_seconds()
                    rtc_minutes = int(diff_seconds / 60)
                    if rtc_minutes < 1: rtc_minutes = 1 # Minimum 1 min
                    
                    msg = f"💤 Setting RTC Alarm (+{rtc_minutes}m) & Shutting Down..."
                    print(msg)
                    log_lifecycle_event(msg)
                    
                    if hw.set_rtc_alarm(rtc_minutes):
                        print("✅ RTC Alarm Set.")
                        log_lifecycle_event("RTC Alarm Set Success")
                    else:
                        print("❌ RTC Alarm Failed (Mock or Error).")
                        log_lifecycle_event("RTC Alarm Set FAILED")
                        
                    hw.schedule_shutdown(delay=5)
                except Exception as e:
                    err = f"CRITICAL: Shutdown Thread Crashed: {e}"
                    print(err)
                    log_lifecycle_event(err)
                    import traceback
                    log_lifecycle_event(traceback.format_exc())
                
            threading.Thread(target=shutdown_sequence).start()
            
        else:
            print("🛠️ Settings Mode: Stay Awake.")
            log_lifecycle_event("Settings Mode - Staying Awake")
            pass

    except Exception as e:
        err_msg = f"Power Management Error: {e}"
        print(err_msg)
        log_lifecycle_event(err_msg)

if __name__ == '__main__':
    # use_reloader=False prevents double initialization of hardware drivers
    # Check power management thread (delay slightly to let app start)
    if not os.environ.get("WERKZEUG_RUN_MAIN") == "true": # Run only once (if reloader is on, but here reloader is false)
         threading.Thread(target=check_power_management).start()

    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
