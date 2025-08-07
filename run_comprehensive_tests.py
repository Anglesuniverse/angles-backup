#!/usr/bin/env python3
"""
Run comprehensive tests on all system components
"""

import subprocess
import sys

def run_test(test_name, command):
    """Run a test and capture results"""
    print(f"\n{'='*50}")
    print(f"TESTING: {test_name}")
    print('='*50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED")
            if result.stdout:
                print("Output:", result.stdout[-500:])  # Last 500 chars
        else:
            print(f"❌ {test_name} FAILED")
            if result.stderr:
                print("Error:", result.stderr[-500:])
            if result.stdout:
                print("Output:", result.stdout[-500:])
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} TIMED OUT")
        return False
    except Exception as e:
        print(f"💥 {test_name} ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        ("Decision Vault Operations", "python test_decision_vault.py"),
        ("Notion Logger (Fixed)", "python test_log.py"),
        ("AI Decision Logger", "python test_ai_decision_logger.py"),
        ("Memory Sync Check", "python fix_memory_sync.py")
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, command in tests:
        if run_test(test_name, command):
            passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL SYSTEMS WORKING!")
    elif passed >= total * 0.75:
        print("✅ Most systems working - minor issues remain")
    else:
        print("❌ Multiple issues need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)