"""
Angles OS™ Health Endpoint Tests
"""
import pytest
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "version" in data
    
    print(f"✅ Health check passed: {data['status']}")
    return True

def test_ping_endpoint():
    """Test ping endpoint"""
    response = requests.get(f"{BASE_URL}/health/ping")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "pong"
    
    print("✅ Ping test passed")
    return True

def test_ready_endpoint():
    """Test readiness check"""
    response = requests.get(f"{BASE_URL}/health/ready")
    
    # Should return 200 if ready, 503 if not
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "ready"
        print("✅ Readiness check passed")
    else:
        print("⚠️ Service not ready yet")
    
    return True

if __name__ == "__main__":
    print("🧪 Running health endpoint tests...")
    
    try:
        test_health_endpoint()
        test_ping_endpoint()
        test_ready_endpoint()
        print("\n🎉 All health tests passed!")
    except Exception as e:
        print(f"\n❌ Health tests failed: {e}")
        exit(1)