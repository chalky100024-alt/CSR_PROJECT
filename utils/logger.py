import logging
import os
import datetime
import sys

# Define path relative to project root (assuming utils is one level deep)
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'debug_network.log')

def setup_debug_logger():
    """
    Sets up a dedicated logger for 'debug_network' that writes to debug_network.log.
    Existing log file is overwritten on startup.
    """
    logger = logging.getLogger('debug_network')
    logger.setLevel(logging.DEBUG)
    
    # Check if handlers already exist to avoid duplication
    if not logger.handlers:
        # File Handler (Append mode 'a' for persistence)
        fh = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        
        logger.addHandler(fh)
        
        # Also print to stdout for journalctl visibility
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        
    logger.info("\n" + "="*50)
    logger.info("=== NEW SESSION STARTED (Persistent Log) ===")
    logger.info("="*50)
    return logger

def log_debug(msg, level='info'):
    """
    Helper to log to the debug_network logger.
    """
    logger = logging.getLogger('debug_network')
    if level.lower() == 'info':
        logger.info(msg)
    elif level.lower() == 'error':
        logger.error(msg)
    elif level.lower() == 'warning':
        logger.warning(msg)
    elif level.lower() == 'debug':
        logger.debug(msg)
        
    # Force flush handlers
    for h in logger.handlers:
        h.flush()

def check_internet_connection():
    """
    Performs a ping test to Google DNS (8.8.8.8) and a HTTP check.
    Returns True if successful, False otherwise.
    """
    import subprocess
    import requests
    
    log_debug("--- STARTUP CONNECTIVITY CHECK ---")
    
    # 1. Ping Check
    try:
        # -c 1: count 1, -W 2: timeout 2s
        cmd = ['ping', '-c', '1', '-W', '2', '8.8.8.8']
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            log_debug("✅ Ping (8.8.8.8): SUCCESS")
        else:
            log_debug(f"❌ Ping (8.8.8.8): FAILED (Code: {res.returncode})")
    except Exception as e:
        log_debug(f"❌ Ping Check Exception: {e}", level='error')
        
    # 2. HTTP Check
    try:
        url = "http://www.google.com"
        t0 = datetime.datetime.now()
        requests.get(url, timeout=5)
        dt = (datetime.datetime.now() - t0).total_seconds()
        log_debug(f"✅ HTTP Check (google.com): SUCCESS ({dt:.2f}s)")
        return True
    except Exception as e:
        log_debug(f"❌ HTTP Check Failed: {e}", level='error')
        return False
