#!/usr/bin/env python3
"""
Comprehensive FastAPI System Test
Tests the Angles AI Universe FastAPI backend alongside the existing system
"""
import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")
    return resp.status_code == 200

def test_vault_system():
    """Test vault ingestion and query"""
    print("\n📚 Testing Vault System...")
    
    # Test ingestion
    print("   Ingesting sample document...")
    vault_data = {
        "source": "Angles AI Universe FastAPI Documentation",
        "chunk": "FastAPI provides modern API capabilities with automatic OpenAPI docs",
        "summary": "FastAPI integration for Angles AI Universe backend system",
        "links": ["https://fastapi.tiangolo.com"]
    }
    
    resp = requests.post(f"{BASE_URL}/vault/ingest", json=vault_data)
    print(f"   Ingest Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   Response: {resp.json()}")
    
    # Test query
    print("   Querying vault...")
    query_data = {"query": "FastAPI documentation", "top_k": 3}
    resp = requests.post(f"{BASE_URL}/vault/query", json=query_data)
    print(f"   Query Status: {resp.status_code}")
    if resp.status_code == 200:
        results = resp.json()
        print(f"   Found {len(results['results'])} results")
        for i, result in enumerate(results['results'][:2]):
            print(f"     {i+1}. {result['source']}: {result['summary'][:50]}...")
    
    return resp.status_code == 200

def test_decision_system():
    """Test decision management system"""
    print("\n🤔 Testing Decision Management System...")
    
    # Create decision
    print("   Creating sample decision...")
    decision_data = {
        "topic": "Choose database technology for FastAPI integration",
        "options": [
            {
                "option": "Use existing Supabase PostgreSQL",
                "pros": ["Already configured", "Proven reliability", "Existing data"],
                "cons": ["Single point of failure"]
            },
            {
                "option": "Add Redis for caching",
                "pros": ["Better performance", "Distributed caching"],
                "cons": ["Additional complexity", "More resources"]
            }
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/decisions", json=decision_data)
    print(f"   Create Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   Error: {resp.text}")
        return False
        
    decision_id = resp.json()["id"]
    print(f"   Created decision ID: {decision_id}")
    
    # Get decision details
    print("   Fetching decision details...")
    resp = requests.get(f"{BASE_URL}/decisions/{decision_id}")
    if resp.status_code == 200:
        decision = resp.json()
        print(f"   Topic: {decision['topic']}")
        print(f"   Options: {len(decision['options'])}")
    
    # Get recommendation
    print("   Getting AI recommendation...")
    resp = requests.post(f"{BASE_URL}/decisions/{decision_id}/recommend", json={})
    if resp.status_code == 200:
        rec = resp.json()
        print(f"   Recommended: {rec['chosen']}")
        print(f"   Rationale: {rec['rationale']}")
    
    # Approve decision
    print("   Approving decision...")
    resp = requests.post(f"{BASE_URL}/decisions/{decision_id}/approve")
    if resp.status_code == 200:
        print(f"   Decision approved: {resp.json()}")
    
    # List decisions
    print("   Listing approved decisions...")
    resp = requests.get(f"{BASE_URL}/decisions?status=approved")
    if resp.status_code == 200:
        decisions = resp.json()
        print(f"   Found {len(decisions)} approved decisions")
    
    return True

def main():
    """Run comprehensive FastAPI test suite"""
    print("🚀 ANGLES AI UNIVERSE™ FASTAPI SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Vault System", test_vault_system),
        ("Decision System", test_decision_system)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
            sleep(0.5)  # Brief pause between tests
        except Exception as e:
            print(f"   ❌ Error in {name}: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"   {name}: {status}")
    
    print(f"\n🏆 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems operational! FastAPI backend ready for production.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    main()