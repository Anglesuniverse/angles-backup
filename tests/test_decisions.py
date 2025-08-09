"""
Angles OS™ Decision Management Tests
"""
import pytest
import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_decision():
    """Test decision creation"""
    test_decision = {
        "topic": "Test decision for Angles OS",
        "options": [
            {
                "option": "Option A",
                "pros": ["Fast implementation", "Low cost"],
                "cons": ["Limited features"]
            },
            {
                "option": "Option B", 
                "pros": ["Comprehensive features", "Future-proof"],
                "cons": ["Higher cost", "Longer implementation"]
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/decisions", json=test_decision)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "decision_id" in data
    assert data["topic"] == test_decision["topic"]
    
    print(f"✅ Decision creation passed: {data['decision_id']}")
    return data["decision_id"]

def test_list_decisions():
    """Test listing decisions"""
    response = requests.get(f"{BASE_URL}/decisions")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "decisions" in data
    assert "total" in data
    
    print(f"✅ Decision listing passed: {data['total']} decisions")
    return True

def test_get_decision(decision_id):
    """Test getting specific decision"""
    response = requests.get(f"{BASE_URL}/decisions/{decision_id}")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == decision_id
    assert "topic" in data
    assert "options" in data
    
    print(f"✅ Get decision passed: {data['topic']}")
    return True

def test_recommend_decision(decision_id):
    """Test decision recommendation"""
    response = requests.post(f"{BASE_URL}/decisions/{decision_id}/recommend", json={})
    
    assert response.status_code == 200
    
    data = response.json()
    assert "chosen" in data
    assert "rationale" in data
    assert data["decision_id"] == decision_id
    
    print(f"✅ Decision recommendation passed: {data['chosen']}")
    return True

def test_approve_decision(decision_id):
    """Test decision approval"""
    response = requests.post(f"{BASE_URL}/decisions/{decision_id}/approve")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["decision_id"] == decision_id
    
    print(f"✅ Decision approval passed")
    return True

def test_decision_stats():
    """Test decision statistics"""
    response = requests.get(f"{BASE_URL}/decisions/stats")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "total_decisions" in data
    assert "by_status" in data
    
    print(f"✅ Decision stats passed: {data['total_decisions']} total")
    return True

if __name__ == "__main__":
    print("🧪 Running decision tests...")
    
    try:
        # Run tests in workflow order
        decision_id = test_create_decision()
        test_list_decisions()
        test_get_decision(decision_id)
        test_recommend_decision(decision_id)
        test_approve_decision(decision_id)
        test_decision_stats()
        
        print("\n🎉 All decision tests passed!")
    except Exception as e:
        print(f"\n❌ Decision tests failed: {e}")
        exit(1)