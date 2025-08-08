#!/usr/bin/env python3
"""
Angles AI Universe™ Deployment Verification
Comprehensive verification of the entire backend deployment

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def setup_logging():
    """Setup logging for deployment verification"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('verify_deployment')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/deployment_verification.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def run_verification():
    """Run complete deployment verification"""
    logger = setup_logging()
    start_time = datetime.now(timezone.utc)
    
    print("🔍 ANGLES AI UNIVERSE™ DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    logger.info("Starting deployment verification")
    
    verification_steps = [
        ("Migration Test", [sys.executable, "run_migration.py", "--dry-run"]),
        ("Health Check", [sys.executable, "backend_monitor.py"]),
        ("Memory Sync Test", [sys.executable, "memory_sync.py", "--test"]),
        ("File AutoSync Test", [sys.executable, "autosync_files.py", "--once", "--dry-run"]),
        ("Comprehensive Tests", [sys.executable, "tests/test_all.py"])
    ]
    
    results = {}
    overall_success = True
    
    for step_name, command in verification_steps:
        logger.info(f"Running {step_name}...")
        print(f"📋 {step_name}...")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            success = result.returncode == 0
            results[step_name] = {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip()
            }
            
            if success:
                print(f"   ✅ PASSED")
                logger.info(f"{step_name} passed")
            else:
                print(f"   ❌ FAILED")
                logger.error(f"{step_name} failed: {result.stderr[:100]}")
                overall_success = False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ TIMEOUT")
            logger.error(f"{step_name} timed out")
            results[step_name] = {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Timeout after 180s'
            }
            overall_success = False
            
        except Exception as e:
            print(f"   💥 ERROR")
            logger.error(f"{step_name} error: {e}")
            results[step_name] = {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
            overall_success = False
    
    # Generate summary
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print()
    print("=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
    
    if overall_success:
        print("✅ DEPLOYMENT VERIFICATION: PASSED")
        logger.info("Deployment verification completed successfully")
    else:
        print("❌ DEPLOYMENT VERIFICATION: FAILED")
        logger.error("Deployment verification failed")
        
        print("\n❌ Failed Tests:")
        for name, result in results.items():
            if not result['success']:
                print(f"   • {name}: {result['stderr'][:100]}...")
    
    print("=" * 60)
    
    # Save results
    verification_results = {
        'timestamp': end_time.isoformat(),
        'duration': duration,
        'overall_success': overall_success,
        'success_rate': success_rate,
        'results': results
    }
    
    try:
        with open('logs/active/verification_results.json', 'w') as f:
            json.dump(verification_results, f, indent=2)
        logger.info("Verification results saved")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = run_verification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Verification failed: {e}")
        sys.exit(1)