#!/usr/bin/env python3
"""
Angles OS™ Post-Run Review System
Auto-detects and fixes common deployment issues
"""
import os
import re
import sys
import subprocess
from pathlib import Path
import json

class AnglesOSReviewer:
    """Post-run review and auto-fix system"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        self.log_files = ['app.log', 'logs/install.log']
        
    def parse_logs(self):
        """Parse log files for common issues"""
        print("📝 Parsing application logs...")
        
        for log_file in self.log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        self.detect_issues(content, log_file)
                except Exception as e:
                    print(f"⚠️ Could not read {log_file}: {e}")
    
    def detect_issues(self, content, source):
        """Detect common deployment issues"""
        # Database connection issues
        if re.search(r'database connection.*failed|psycopg2.*error', content, re.IGNORECASE):
            self.issues_found.append({
                'type': 'database_connection',
                'source': source,
                'message': 'Database connection failure detected'
            })
        
        # Missing imports
        import_errors = re.findall(r'ModuleNotFoundError: No module named \'([^\']+)\'', content)
        for module in import_errors:
            self.issues_found.append({
                'type': 'missing_import',
                'source': source,
                'message': f'Missing module: {module}',
                'module': module
            })
        
        # Environment variable issues
        env_errors = re.findall(r'KeyError.*env.*\'([^\']+)\'|environment variable.*\'([^\']+)\'.*not set', content, re.IGNORECASE)
        for match in env_errors:
            env_var = match[0] or match[1]
            self.issues_found.append({
                'type': 'missing_env_var',
                'source': source,
                'message': f'Missing environment variable: {env_var}',
                'env_var': env_var
            })
        
        # API endpoint errors
        if re.search(r'404.*not found|endpoint.*not.*found', content, re.IGNORECASE):
            self.issues_found.append({
                'type': 'endpoint_error',
                'source': source,
                'message': 'API endpoint not found errors detected'
            })
    
    def run_pytest(self):
        """Run pytest and capture results"""
        print("🧪 Running test suite...")
        
        try:
            result = subprocess.run(['python', '-m', 'pytest', '-q'], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ All tests passed")
                return True
            else:
                print(f"❌ Tests failed with return code {result.returncode}")
                print(f"Output: {result.stdout}")
                print(f"Errors: {result.stderr}")
                
                # Parse test failures
                self.detect_issues(result.stdout + result.stderr, 'pytest')
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Tests timed out after 60 seconds")
            return False
        except FileNotFoundError:
            print("⚠️ pytest not available, skipping tests")
            return None
    
    def apply_fixes(self):
        """Apply automatic fixes for detected issues"""
        print("🔧 Applying automatic fixes...")
        
        for issue in self.issues_found:
            if issue['type'] == 'missing_env_var':
                self.fix_missing_env_var(issue)
            elif issue['type'] == 'missing_import':
                self.fix_missing_import(issue)
            elif issue['type'] == 'database_connection':
                self.fix_database_connection(issue)
    
    def fix_missing_env_var(self, issue):
        """Fix missing environment variables"""
        env_var = issue['env_var']
        
        # Add common environment variables with defaults
        defaults = {
            'POSTGRES_URL': 'postgresql://postgres:postgres@localhost:5432/angles_os',
            'REDIS_URL': 'redis://localhost:6379',
            'LOG_LEVEL': 'INFO',
            'ENV': 'development'
        }
        
        if env_var in defaults:
            # Check if already in .env
            env_file = Path('.env')
            if env_file.exists():
                content = env_file.read_text()
                if env_var not in content:
                    with open('.env', 'a') as f:
                        f.write(f'\n{env_var}={defaults[env_var]}\n')
                    self.fixes_applied.append(f"Added {env_var} to .env")
            else:
                # Create .env file
                with open('.env', 'w') as f:
                    f.write(f'{env_var}={defaults[env_var]}\n')
                self.fixes_applied.append(f"Created .env with {env_var}")
    
    def fix_missing_import(self, issue):
        """Fix missing imports (informational only - requires manual action)"""
        module = issue['module']
        print(f"⚠️ Missing module '{module}' - install with: pip install {module}")
        self.fixes_applied.append(f"Identified missing module: {module}")
    
    def fix_database_connection(self, issue):
        """Fix database connection issues"""
        print("🗄️ Database connection issue detected")
        print("💡 Suggested fixes:")
        print("   1. Ensure PostgreSQL is running")
        print("   2. Check POSTGRES_URL environment variable")
        print("   3. Run: python scripts/run_migration.py")
        
        self.fixes_applied.append("Provided database connection troubleshooting steps")
    
    def health_check(self):
        """Perform basic health check"""
        print("🏥 Running health check...")
        
        health_results = {
            'database_migration': False,
            'api_startup': False,
            'redis_connection': False
        }
        
        # Check if migration script exists and can be run
        migration_script = Path('scripts/run_migration.py')
        if migration_script.exists():
            try:
                result = subprocess.run(['python', str(migration_script)], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    health_results['database_migration'] = True
                    print("✅ Database migration successful")
                else:
                    print(f"❌ Database migration failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("⏰ Database migration timed out")
            except Exception as e:
                print(f"❌ Database migration error: {e}")
        
        # Check if FastAPI can start (basic import test)
        try:
            subprocess.run(['python', '-c', 'from api.main import app; print("FastAPI import successful")'], 
                          check=True, capture_output=True, text=True, timeout=10)
            health_results['api_startup'] = True
            print("✅ FastAPI import successful")
        except subprocess.CalledProcessError as e:
            print(f"❌ FastAPI import failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            print("⏰ FastAPI import timed out")
        
        return health_results
    
    def generate_report(self, test_results, health_results):
        """Generate final review report"""
        print("\n" + "="*60)
        print("📋 ANGLES OS™ POST-RUN REVIEW REPORT")
        print("="*60)
        
        # Summary
        issues_count = len(self.issues_found)
        fixes_count = len(self.fixes_applied)
        
        print(f"🔍 Issues found: {issues_count}")
        print(f"🔧 Fixes applied: {fixes_count}")
        
        # Test results
        if test_results is True:
            print("🧪 Tests: ✅ PASSED")
        elif test_results is False:
            print("🧪 Tests: ❌ FAILED")
        else:
            print("🧪 Tests: ⚠️ SKIPPED")
        
        # Health check results
        print("\n🏥 Health Check Results:")
        for check, status in health_results.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {check.replace('_', ' ').title()}")
        
        # Issues detail
        if self.issues_found:
            print(f"\n🚨 Issues Found:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"   {i}. {issue['message']} (in {issue['source']})")
        
        # Fixes applied
        if self.fixes_applied:
            print(f"\n✅ Fixes Applied:")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"   {i}. {fix}")
        
        # Overall status
        healthy_checks = sum(health_results.values())
        total_checks = len(health_results)
        
        if test_results is True and healthy_checks == total_checks and issues_count == 0:
            print(f"\n🎉 ANGLES OS™ DEPLOYMENT: SUCCESS")
            print("   All systems operational and ready for production!")
            return True
        elif healthy_checks > 0:
            print(f"\n⚠️ ANGLES OS™ DEPLOYMENT: PARTIAL")
            print(f"   {healthy_checks}/{total_checks} health checks passed")
            print("   Review issues above and rerun deployment")
            return False
        else:
            print(f"\n❌ ANGLES OS™ DEPLOYMENT: FAILED")
            print("   Critical issues prevent successful deployment")
            return False
    
    def run_review(self):
        """Execute complete review process"""
        print("🚀 Starting Angles OS™ Post-Run Review")
        print("="*60)
        
        # Parse logs
        self.parse_logs()
        
        # Run tests
        test_results = self.run_pytest()
        
        # Apply fixes
        self.apply_fixes()
        
        # Health check
        health_results = self.health_check()
        
        # Generate report
        success = self.generate_report(test_results, health_results)
        
        # Save report to file
        report_data = {
            'timestamp': str(__import__('datetime').datetime.now()),
            'issues_found': self.issues_found,
            'fixes_applied': self.fixes_applied,
            'test_results': test_results,
            'health_results': health_results,
            'overall_success': success
        }
        
        with open('run_review.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: run_review.json")
        
        return success

def main():
    """Main entry point"""
    reviewer = AnglesOSReviewer()
    success = reviewer.run_review()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()