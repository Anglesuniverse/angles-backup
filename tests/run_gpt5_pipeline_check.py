#!/usr/bin/env python3
"""
Angles AI Universe™ GPT-5 Pipeline Integration Test
End-to-end verification of complete GPT-5 decision processing pipeline

Author: Angles AI Universe™ Testing Team
Version: 1.0.0 - Pipeline Verification
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_test_logging():
    """Setup logging for pipeline tests"""
    os.makedirs("test_results", exist_ok=True)
    
    logger = logging.getLogger('pipeline_test')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    log_file = f"test_results/pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

def test_ai_client_pipeline():
    """Test 1: AI Client Pipeline Functionality"""
    print("🧪 Test 1: AI Client Pipeline")
    
    try:
        from tools.ai_client import get_client, analyze_decision_with_gpt5, get_ai_enhancement_status
        
        # Check AI status
        status = get_ai_enhancement_status()
        if not status['client_ready']:
            print("❌ AI client not ready for pipeline testing")
            return False
        
        print(f"✅ AI client ready - Model: {status['current_model']}")
        
        # Test decision analysis
        client = get_client()
        test_decision = "Implement GraphQL API to replace REST endpoints for better data fetching efficiency"
        
        # Note: analyze_decision_with_gpt5 is async, but we'll test the sync path
        print(f"🔍 Testing decision analysis for: {test_decision[:50]}...")
        
        # We'll test this through the memory bridge instead since it has sync methods
        from memory_bridge import AIEnhancedMemoryBridge
        bridge = AIEnhancedMemoryBridge(enable_ai=True)
        
        result = bridge.classify_decision(test_decision)
        
        if result and isinstance(result, dict):
            print(f"✅ AI analysis successful")
            print(f"   Type: {result.get('type', 'unknown')}")
            print(f"   Priority: {result.get('priority', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
            return True
        else:
            print("❌ AI analysis failed or returned invalid result")
            return False
            
    except Exception as e:
        print(f"❌ AI client pipeline test failed: {e}")
        return False

def test_memory_bridge_pipeline():
    """Test 2: Memory Bridge Pipeline"""
    print("\n🧪 Test 2: Memory Bridge Pipeline")
    
    try:
        from memory_bridge import AIEnhancedMemoryBridge
        
        bridge = AIEnhancedMemoryBridge(enable_ai=True)
        
        # Test multiple decision types
        test_decisions = [
            "Adopt microservices architecture for scalability",
            "Implement OAuth 2.0 for user authentication", 
            "Use Redis for caching frequently accessed data",
            "Establish code review process for all pull requests",
            "Migrate from MySQL to PostgreSQL for better performance"
        ]
        
        results = []
        
        for i, decision in enumerate(test_decisions, 1):
            print(f"🔍 Processing decision {i}/{len(test_decisions)}: {decision[:40]}...")
            
            analysis = bridge.classify_decision(decision)
            
            if analysis and isinstance(analysis, dict):
                results.append({
                    'decision': decision,
                    'analysis': analysis,
                    'success': True
                })
                print(f"   ✅ Type: {analysis.get('type', 'unknown')} | Priority: {analysis.get('priority', 'unknown')}")
            else:
                results.append({
                    'decision': decision,
                    'analysis': None,
                    'success': False
                })
                print(f"   ❌ Analysis failed")
        
        success_count = sum(1 for r in results if r['success'])
        success_rate = (success_count / len(test_decisions)) * 100
        
        print(f"📊 Memory Bridge Pipeline Results: {success_count}/{len(test_decisions)} ({success_rate:.1f}% success)")
        
        if success_rate >= 80:
            print("✅ Memory Bridge pipeline performing well")
            return True
        else:
            print("⚠️ Memory Bridge pipeline has issues")
            return False
            
    except Exception as e:
        print(f"❌ Memory Bridge pipeline test failed: {e}")
        return False

def test_decision_enhancement_pipeline():
    """Test 3: Decision Enhancement Pipeline"""
    print("\n🧪 Test 3: Decision Enhancement Pipeline")
    
    try:
        from memory_sync import MemorySync
        
        # Use dry run to avoid actual database operations
        sync = MemorySync(dry_run=True)
        
        if not hasattr(sync, 'enhance_decision_with_ai'):
            print("❌ enhance_decision_with_ai method not found in MemorySync")
            return False
        
        # Test decision enhancement
        test_decisions = [
            {
                'id': 'test-001',
                'decision': 'Implement continuous integration pipeline with automated testing',
                'date': '2025-08-08',
                'type': 'technical',
                'active': True
            },
            {
                'id': 'test-002',
                'decision': 'Establish data retention policy for user analytics',
                'date': '2025-08-08',
                'type': 'process',
                'active': True
            }
        ]
        
        enhanced_results = []
        
        for decision in test_decisions:
            print(f"🔍 Enhancing: {decision['decision'][:40]}...")
            
            enhanced = sync.enhance_decision_with_ai(decision)
            
            if enhanced.get('ai_enhanced') and 'ai_analysis' in enhanced:
                enhanced_results.append(True)
                analysis = enhanced['ai_analysis']
                print(f"   ✅ Enhanced - Type: {analysis.get('type', 'unknown')}")
                print(f"      AI Timestamp: {enhanced.get('ai_timestamp', 'N/A')}")
            else:
                enhanced_results.append(False)
                print(f"   ❌ Enhancement failed")
        
        success_rate = (sum(enhanced_results) / len(test_decisions)) * 100
        print(f"📊 Enhancement Pipeline Results: {sum(enhanced_results)}/{len(test_decisions)} ({success_rate:.1f}% success)")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Decision enhancement pipeline test failed: {e}")
        return False

def test_full_memory_sync_pipeline():
    """Test 4: Full Memory Sync Pipeline (Dry Run)"""
    print("\n🧪 Test 4: Full Memory Sync Pipeline")
    
    try:
        from memory_sync import MemorySync
        
        # Initialize with dry run
        sync = MemorySync(dry_run=True)
        
        print("🔍 Testing connection setup...")
        if not sync.test_connections():
            print("⚠️ Some connections failed, but continuing with available services")
        
        # Test AI bridge initialization
        if hasattr(sync, 'ai_bridge') and sync.ai_bridge:
            print("✅ AI bridge initialized in MemorySync")
        else:
            print("⚠️ AI bridge not available in MemorySync")
            return False
        
        # Test enhanced sync process simulation
        print("🔍 Simulating enhanced sync process...")
        
        # This would normally fetch real decisions, but we'll test the enhancement logic
        mock_decision = {
            'id': 'pipeline-test-123',
            'decision': 'Adopt Infrastructure as Code using Terraform for environment management',
            'date': '2025-08-08',
            'type': 'technical'
        }
        
        # Test the enhancement
        enhanced = sync.enhance_decision_with_ai(mock_decision)
        
        if enhanced.get('ai_enhanced'):
            print("✅ Full pipeline enhancement successful")
            print(f"   Analysis: {enhanced['ai_analysis'].get('type', 'unknown')}")
            print(f"   Priority: {enhanced['ai_analysis'].get('priority', 'unknown')}")
            return True
        else:
            print("❌ Full pipeline enhancement failed")
            return False
        
    except Exception as e:
        print(f"❌ Full memory sync pipeline test failed: {e}")
        return False

def test_error_handling_pipeline():
    """Test 5: Error Handling in Pipeline"""
    print("\n🧪 Test 5: Error Handling Pipeline")
    
    try:
        from memory_sync import MemorySync
        
        sync = MemorySync(dry_run=True)
        
        # Test with invalid decision data
        invalid_decisions = [
            {},  # Empty decision
            {'id': 'test', 'decision': ''},  # Empty decision text
            {'id': 'test', 'decision': None},  # None decision text
        ]
        
        error_handling_results = []
        
        for i, invalid_decision in enumerate(invalid_decisions, 1):
            print(f"🔍 Testing error handling {i}/3...")
            
            try:
                enhanced = sync.enhance_decision_with_ai(invalid_decision)
                
                # Should still return a decision object, possibly with errors
                if isinstance(enhanced, dict):
                    error_handling_results.append(True)
                    print(f"   ✅ Graceful error handling")
                else:
                    error_handling_results.append(False)
                    print(f"   ❌ Poor error handling")
                    
            except Exception as e:
                error_handling_results.append(False)
                print(f"   ❌ Unhandled exception: {e}")
        
        success_rate = (sum(error_handling_results) / len(invalid_decisions)) * 100
        print(f"📊 Error Handling Results: {sum(error_handling_results)}/{len(invalid_decisions)} ({success_rate:.1f}% graceful)")
        
        return success_rate >= 100  # Should handle all errors gracefully
        
    except Exception as e:
        print(f"❌ Error handling pipeline test failed: {e}")
        return False

def test_performance_pipeline():
    """Test 6: Pipeline Performance"""
    print("\n🧪 Test 6: Pipeline Performance")
    
    try:
        from memory_bridge import AIEnhancedMemoryBridge
        
        bridge = AIEnhancedMemoryBridge(enable_ai=True)
        
        # Test multiple decisions for performance
        test_decision = "Implement load balancing with NGINX for high availability"
        
        print("🔍 Testing pipeline performance (5 iterations)...")
        
        times = []
        for i in range(5):
            start_time = time.time()
            result = bridge.classify_decision(test_decision)
            end_time = time.time()
            
            duration = end_time - start_time
            times.append(duration)
            
            if result:
                print(f"   Iteration {i+1}: {duration:.2f}s ✅")
            else:
                print(f"   Iteration {i+1}: {duration:.2f}s ❌")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"📊 Performance Results:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   Range: {min_time:.2f}s - {max_time:.2f}s")
        
        # Performance thresholds
        if avg_time <= 10.0:  # Should complete within 10 seconds on average
            print("✅ Performance within acceptable limits")
            return True
        else:
            print("⚠️ Performance may need optimization")
            return False
        
    except Exception as e:
        print(f"❌ Performance pipeline test failed: {e}")
        return False

def run_pipeline_test_suite():
    """Run complete pipeline test suite"""
    logger, log_file = setup_test_logging()
    
    print("🚀 ANGLES AI UNIVERSE™ GPT-5 PIPELINE VERIFICATION")
    print("=" * 65)
    print(f"📅 Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📄 Log File: {log_file}")
    print("=" * 65)
    
    tests = [
        ("AI Client Pipeline", test_ai_client_pipeline),
        ("Memory Bridge Pipeline", test_memory_bridge_pipeline),
        ("Decision Enhancement Pipeline", test_decision_enhancement_pipeline),
        ("Full Memory Sync Pipeline", test_full_memory_sync_pipeline),
        ("Error Handling Pipeline", test_error_handling_pipeline),
        ("Performance Pipeline", test_performance_pipeline)
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    start_time = time.time()
    
    for test_name, test_func in tests:
        logger.info(f"Starting test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                passed += 1
                logger.info(f"Test passed: {test_name}")
            else:
                logger.warning(f"Test failed: {test_name}")
        except Exception as e:
            logger.error(f"Test failed with exception: {test_name} - {e}")
            results.append((test_name, False))
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print("\n" + "=" * 65)
    print("📊 PIPELINE VERIFICATION RESULTS")
    print("=" * 65)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📈 Summary:")
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Tests Failed: {total - passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    print(f"   Total Duration: {total_duration:.2f}s")
    
    if passed == total:
        print("\n🎉 ALL PIPELINE TESTS PASSED - GPT-5 INTEGRATION FULLY OPERATIONAL!")
        status = "OPERATIONAL"
    elif passed >= total * 0.8:
        print("\n⚠️ MOSTLY OPERATIONAL - Pipeline working with minor issues")
        status = "MOSTLY_OPERATIONAL"
    elif passed >= total * 0.5:
        print("\n⚠️ PARTIALLY OPERATIONAL - Pipeline has significant issues")
        status = "PARTIALLY_OPERATIONAL"
    else:
        print("\n❌ PIPELINE VERIFICATION FAILED - Major integration issues")
        status = "FAILED"
    
    # Generate pipeline report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "tests_total": total,
        "tests_passed": passed,
        "tests_failed": total - passed,
        "success_rate": (passed/total)*100,
        "total_duration": total_duration,
        "test_results": [{"name": name, "passed": result} for name, result in results],
        "environment": {
            "openai_api_key_configured": bool(os.getenv('OPENAI_API_KEY')),
            "fallback_mode": os.getenv('USE_GPT4O_FALLBACK', '').lower() == 'true'
        }
    }
    
    # Save report
    report_file = f"test_results/pipeline_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Pipeline verification report saved: {report_file}")
    print(f"📄 Detailed logs saved: {log_file}")
    print("=" * 65)
    
    logger.info(f"Pipeline verification completed - Status: {status}")
    
    return status == "OPERATIONAL"

if __name__ == "__main__":
    success = run_pipeline_test_suite()
    sys.exit(0 if success else 1)