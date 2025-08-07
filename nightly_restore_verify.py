#!/usr/bin/env python3
"""
Nightly Restore Verification for Angles AI Universe™
Runs automated dry-run restore verification and logs results

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

def setup_logging():
    """Setup verification logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('restore_verify')
    logger.setLevel(logging.INFO)
    
    # File handler for verification logs
    file_handler = logging.FileHandler('logs/restore_verify.log')
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
    """Run nightly restore verification"""
    logger = setup_logging()
    
    print()
    print("🌙 NIGHTLY RESTORE VERIFICATION")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    logger.info("Starting nightly restore verification")
    
    try:
        # Run dry-run restore verification
        logger.info("Executing: python run_restore_now.py --dry-run")
        
        result = subprocess.run([
            sys.executable, 'run_restore_now.py', '--dry-run'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("✅ Verification successful")
            print("✅ RESTORE VERIFICATION: SUCCESS")
            print("   • Backup files are accessible")
            print("   • Git repository is synchronized")
            print("   • Restore system is functional")
            print("   • Environment variables are valid")
            
            # Log output summary
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines[-10:]:  # Last 10 lines of output
                    if line.strip() and ('SUCCESS' in line or 'records' in line or 'files' in line):
                        logger.info(f"Output: {line.strip()}")
            
            return True
            
        else:
            logger.error("❌ Verification failed")
            print("❌ RESTORE VERIFICATION: FAILED")
            print(f"   • Exit code: {result.returncode}")
            
            if result.stderr:
                print(f"   • Error: {result.stderr.strip()}")
                logger.error(f"Error output: {result.stderr.strip()}")
            
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Verification timed out after 5 minutes")
        print("❌ RESTORE VERIFICATION: TIMEOUT")
        print("   • Verification took longer than 5 minutes")
        return False
        
    except FileNotFoundError:
        logger.error("❌ run_restore_now.py not found")
        print("❌ RESTORE VERIFICATION: FILE NOT FOUND")
        print("   • run_restore_now.py script is missing")
        return False
        
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        print(f"❌ RESTORE VERIFICATION: ERROR")
        print(f"   • {e}")
        return False
    
    finally:
        print()
        print("=" * 40)
        print("Verification completed")
        print(f"Check logs/restore_verify.log for details")
        print()

def main():
    """Main entry point"""
    success = run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()