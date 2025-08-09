"""
Angles OS™ TokenVault Tests
"""
import pytest
import requests
import json

BASE_URL = "http://localhost:8000"

def test_vault_ingest():
    """Test vault ingestion"""
    test_data = {
        "source": "test_source",
        "chunk": "This is a test chunk for the Angles OS vault system",
        "summary": "Test chunk for validation",
        "links": ["http://test.com"]
    }
    
    response = requests.post(f"{BASE_URL}/vault/ingest", json=test_data)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "chunk_id" in data
    
    print(f"✅ Vault ingestion passed: {data['chunk_id']}")
    return data["chunk_id"]

def test_vault_query():
    """Test vault querying"""
    query_data = {
        "query": "test chunk",
        "top_k": 5
    }
    
    response = requests.post(f"{BASE_URL}/vault/query", json=query_data)
    
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    assert "query" in data
    assert data["query"] == "test chunk"
    
    print(f"✅ Vault query passed: {len(data['results'])} results")
    return True

def test_vault_stats():
    """Test vault statistics"""
    response = requests.get(f"{BASE_URL}/vault/stats")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "total_chunks" in data
    
    print(f"✅ Vault stats passed: {data['total_chunks']} total chunks")
    return True

def test_vault_by_source():
    """Test getting chunks by source"""
    response = requests.get(f"{BASE_URL}/vault/source/test_source")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "chunks" in data
    assert data["source"] == "test_source"
    
    print(f"✅ Vault by source passed: {len(data['chunks'])} chunks")
    return True

if __name__ == "__main__":
    print("🧪 Running vault tests...")
    
    try:
        # Run tests in order
        chunk_id = test_vault_ingest()
        test_vault_query()
        test_vault_stats()
        test_vault_by_source()
        
        print("\n🎉 All vault tests passed!")
    except Exception as e:
        print(f"\n❌ Vault tests failed: {e}")
        exit(1)