#!/usr/bin/env python3
"""
Debug FastAPI routes
"""
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

def debug_routes():
    print("Registered routes:")
    for route in app.routes:
        print(f"  {route.methods} {route.path}")

if __name__ == "__main__":
    debug_routes()