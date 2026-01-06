
import sys
import os
import traceback

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing Update Flow...")
    import photo_frame
    
    # 1. Initialize
    print("Initializing Frame...")
    pf = photo_frame.EInkPhotoFrame()
    
    # 2. Run Refresh (this calls renderer internally)
    print("Calling refresh_display...")
    pf.refresh_display()
    
    print("SUCCESS: refresh_display finished without error.")
    
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    traceback.print_exc()
