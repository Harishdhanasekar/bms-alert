import time
import subprocess
import sys
from datetime import datetime

def main():
    # Force output encoding to UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=========================================================")
    print("🚀 Starting local BookMyShow Alert Loop")
    print("   Checking every 5 minutes. Press Ctrl+C to stop.")
    print("=========================================================")
    
    python_exe = sys.executable  # Uses the current Python interpreter
    
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Running check...")
        
        try:
            # Execute monitor.py
            result = subprocess.run(
                [python_exe, "monitor.py"],
                capture_output=True,
                text=True
            )
            
            # Print stdout and stderr from monitor.py
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(f"[ERR] {result.stderr.strip()}", file=sys.stderr)
                
        except Exception as e:
            print(f"[ERR] Failed to execute monitor.py: {e}", file=sys.stderr)
            
        # Wait for 5 minutes (300 seconds)
        time.sleep(300)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Local loop stopped by user.")
