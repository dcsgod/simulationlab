"""
Health check and system diagnostics endpoints.
"""
from fastapi import APIRouter
import time
import sys

router = APIRouter(tags=["Health"])


@router.get("/api/health")
def get_health():
    return {
        "status": "healthy",
        "service": "simulation-lab-api",
        "timestamp": time.time(),
        "python_version": sys.version,
    }
