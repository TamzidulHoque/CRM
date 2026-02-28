#!/usr/bin/env python3
import sys
import os

print("Python version:", sys.version)
print("Working directory:", os.getcwd())
print("Python path:", sys.path[:3])

print("\n--- Attempting to import app ---")
try:
    from backend.app.main import app
    print("✓ App imported successfully!")
    print(f"✓ App title: {app.title}")
    print(f"✓ App routes: {len(app.routes)}")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n--- App import successful! ---")
