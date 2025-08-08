#!/usr/bin/env python3
"""
Angles AI Universe™ GPT-5 Activation Test Suite
Comprehensive verification of GPT-5 integration and functionality

Author: Angles AI Universe™ Testing Team
Version: 1.0.0 - GPT-5 Verification
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ai_client_import():
    """Test 1: Verify AI client can be imported"""
    print("🧪 Test 1: AI Client Import")
    try:
        from tools.ai_client import get_client, get_model, analyze_decision_with_gpt5, test_gpt5_connection
        print("✅ AI client modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ AI client import failed: {e}")
        return False

def test_memory_bridge_import():
    """Test 2: Verify memory bridge with AI can be imported"""
    print("\n🧪 Test 2: Memory Bridge AI Import")
    try:
        from memory_bridge import AIEnhancedMemoryBridge
        print("✅ AI Enhanced Memory Bridge imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Memory Bridge import failed: {e}")
        return False

def test_openai_package():
    """Test 3: Verify OpenAI package availability"""
    print("\n🧪 Test 3: OpenAI Package Availability")
    try:
        import openai
        from openai import OpenAI
        print(f"✅ OpenAI package available (version: {openai.__version__ if hasattr(openai, '__version__') else 'unknown'})")
        return True
    except ImportError as e:
        print(f"❌ OpenAI package not available: {e}")
        return False

def test_environment_variables():
    """Test 4: Verify required environment variables"""
    print("\n🧪 Test 4: Environment Variables")
    
    required_vars = ['OPENAI_API_KEY']
    optional_vars = ['USE_GPT4O_FALLBACK']
    
    results = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 8}...{value[-4:] if len(value) > 4 else '****'}")
            results[var] = True
        else:
            print(f"❌ {var}: Not found")
            results[var] = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"ℹ️ {var}: {value}")
        else:
            print(f"ℹ️ {var}: Not set (default behavior)")
    
    return all(results.values())

def test_ai_client_initialization():
    """Test 5: Verify AI client can be initialized"""
    print("\n🧪 Test 5: AI Client Initialization")
    try:
        from tools.ai_client import get_client, get_model
        
        client = get_client()
        model = get_model()
        
        if client:
            print(f"✅ OpenAI client initialized successfully")
            print(f"✅ Model configured: {model}")
            return True
        else:
            print("❌ Failed to initialize OpenAI client")
            return False
    except Exception as e:
        print(f"❌ AI client initialization failed: {e}")
        return False

def test_gpt5_connection():
    """Test 6: Verify GPT-5 connection and response"""
    print("\n🧪 Test 6: GPT-5 Connection Test")
    try:
        from tools.ai_client import test_gpt5_connection
        
        result = test_gpt5_connection()
        
        if result['test_successful']:
            print(f"✅ GPT-5 connection successful")
            print(f"✅ Model: {result['model']}")
            print(f"✅ Response: {result.get('response', 'N/A')}")
            return True
        else:
            print(f"❌ GPT-5 connection failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ GPT-5 connection test failed: {e}")
        return False

def test_memory_bridge_initialization():
    """Test 7: Verify AI Enhanced Memory Bridge initialization"""
    print("\n🧪 Test 7: Memory Bridge Initialization")
    try:
        from memory_bridge import AIEnhancedMemoryBridge
        
        # Test with AI enabled
        bridge = AIEnhancedMemoryBridge(enable_ai=True)
        
        if hasattr(bridge, 'enable_ai') and bridge.enable_ai:
            print("✅ Memory Bridge with AI enabled successfully")
            return True
        else:
            print("⚠️ Memory Bridge initialized but AI features disabled")
            return False
    except Exception as e:
        print(f"❌ Memory Bridge initialization failed: {e}")
        return False

def test_decision_analysis():
    """Test 8: Verify decision analysis functionality"""
    print("\n🧪 Test 8: Decision Analysis Test")
    try:
        from memory_bridge import AIEnhancedMemoryBridge
        
        bridge = AIEnhancedMemoryBridge(enable_ai=True)
        
        # Test decision
        test_decision = "Implement microservices architecture for better scalability and maintainability"
        
        result = bridge.classify_decision(test_decision)
        
        if result and isinstance(result, dict):
            print(f"✅ Decision analysis completed")
            print(f"   Type: {result.get('type', 'unknown')}")
            print(f"   Priority: {result.get('priority', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0.0)}")
            
            # Check for required fields
            required_fields = ['type', 'priority', 'confidence']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                print("✅ All required analysis fields present")
                return True
            else:
                print(f"⚠️ Missing analysis fields: {missing_fields}")
                return False
        else:
            print("❌ Decision analysis returned invalid result")
            return False
    except Exception as e:
        print(f"❌ Decision analysis test failed: {e}")
        return False

def test_memory_sync_integration():
    """Test 9: Verify memory sync AI integration"""
    print("\n🧪 Test 9: Memory Sync AI Integration")
    try:
        from memory_sync import MemorySync
        
        # Initialize with dry run to avoid actual sync
        sync = MemorySync(dry_run=True)
        
        if hasattr(sync, 'ai_bridge') and sync.ai_bridge:
            print("✅ Memory Sync initialized with AI bridge")
            
            # Test the enhance_decision_with_ai method
            if hasattr(sync, 'enhance_decision_with_ai'):
                test_decision = {
                    'id': 'test-123',
                    'decision': 'Adopt containerization with Docker for deployment',
                    'date': '2025-08-08',
                    'type': 'technical'
                }
                
                enhanced = sync.enhance_decision_with_ai(test_decision)
                
                if enhanced.get('ai_enhanced') and 'ai_analysis' in enhanced:
                    print("✅ Decision enhancement working correctly")
                    print(f"   AI Analysis Type: {enhanced['ai_analysis'].get('type', 'unknown')}")
                    return True
                else:
                    print("❌ Decision enhancement not working properly")
                    return False
            else:
                print("❌ enhance_decision_with_ai method not found")
                return False
        else:
            print("⚠️ Memory Sync initialized but AI bridge not available")
            return False
    except Exception as e:
        print(f"❌ Memory Sync integration test failed: {e}")
        return False

def test_ai_enhancement_status():
    """Test 10: Verify overall AI enhancement status"""
    print("\n🧪 Test 10: AI Enhancement Status")
    try:
        from tools.ai_client import get_ai_enhancement_status
        
        status = get_ai_enhancement_status()
        
        print(f"📊 AI Enhancement Status Report:")
        print(f"   OpenAI Package: {'✅' if status['openai_package_available'] else '❌'}")
        print(f"   API Key: {'✅' if status['api_key_configured'] else '❌'}")
        print(f"   Client Ready: {'✅' if status['client_ready'] else '❌'}")
        print(f"   Model: {status['current_model']}")
        print(f"   Features: {len([f for f in status['features'].values() if f])} enabled")
        
        # Check if core functionality is available
        core_ready = (
            status['openai_package_available'] and
            status['api_key_configured'] and
            status['client_ready']
        )
        
        if core_ready:
            print("✅ All core AI features are ready")
            return True
        else:
            print("⚠️ Some AI features may be limited")
            return False
    except Exception as e:
        print(f"❌ AI enhancement status check failed: {e}")
        return False

def run_verification_suite():
    """Run complete GPT-5 verification suite"""
    print("🚀 ANGLES AI UNIVERSE™ GPT-5 ACTIVATION VERIFICATION")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    tests = [
        test_ai_client_import,
        test_memory_bridge_import,
        test_openai_package,
        test_environment_variables,
        test_ai_client_initialization,
        test_gpt5_connection,
        test_memory_bridge_initialization,
        test_decision_analysis,
        test_memory_sync_integration,
        test_ai_enhancement_status
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION RESULTS")
    print("=" * 60)
    print(f"✅ Tests Passed: {passed}/{total}")
    print(f"❌ Tests Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - GPT-5 INTEGRATION FULLY OPERATIONAL!")
        status = "OPERATIONAL"
    elif passed >= total * 0.8:
        print("\n⚠️ MOSTLY OPERATIONAL - Some non-critical features may be limited")
        status = "MOSTLY_OPERATIONAL"
    elif passed >= total * 0.5:
        print("\n⚠️ PARTIALLY OPERATIONAL - Core features available but degraded")
        status = "PARTIALLY_OPERATIONAL"
    else:
        print("\n❌ VERIFICATION FAILED - GPT-5 integration not ready")
        status = "FAILED"
    
    # Generate verification report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "tests_total": total,
        "tests_passed": passed,
        "tests_failed": total - passed,
        "success_rate": (passed/total)*100,
        "test_results": results,
        "environment": {
            "openai_api_key_configured": bool(os.getenv('OPENAI_API_KEY')),
            "fallback_mode": os.getenv('USE_GPT4O_FALLBACK', '').lower() == 'true'
        }
    }
    
    # Save report
    os.makedirs("test_results", exist_ok=True)
    report_file = f"test_results/gpt5_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Verification report saved: {report_file}")
    print("=" * 60)
    
    return status == "OPERATIONAL"

if __name__ == "__main__":
    success = run_verification_suite()
    sys.exit(0 if success else 1)