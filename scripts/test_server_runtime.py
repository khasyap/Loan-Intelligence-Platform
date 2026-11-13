"""
Test Server Runner: Starts uvicorn in a subprocess, runs verify_runtime_live.py, then terminates.
"""
import subprocess
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.verify_runtime_live import run_live_verification

def main():
    print("Starting uvicorn backend on 127.0.0.1:8000...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be responsive
    time.sleep(3)
    
    try:
        run_live_verification()
    finally:
        print("\nStopping uvicorn backend...")
        proc.terminate()
        proc.wait(timeout=5)
        print("Server stopped cleanly.")

if __name__ == "__main__":
    main()
