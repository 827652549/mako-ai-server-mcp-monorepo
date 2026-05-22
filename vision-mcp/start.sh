#!/bin/bash
set -e
echo "=== Python version ===" 
python3 --version
echo "=== Testing imports ===" 
python3 -c "
import sys, traceback
try:
    import app.main
    print(\"imports OK\")
except Exception:
    traceback.print_exc()
    sys.exit(1)
"
echo "=== Starting uvicorn ===" 
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --no-access-log
