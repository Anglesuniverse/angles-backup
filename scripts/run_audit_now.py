#!/usr/bin/env python3
"""
Angles AI Universe™ Panic Kit - One-Click Manual Audit System
Emergency audit runner for immediate system validation

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

class PanicKitAuditRunner:
    """Emergency one-click audit system runner"""
    
    def __init__(self):
        """Initialize panic kit audit runner"""
        self.setup_logging()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Audit configuration
        self.config = {
            'timeout_per_audit': 600,  # 10 minutes per audit
            'critical_threshold': 1,   # Exit on 1+ critical findings
            'continue_on_failure': True,  # Continue even if one audit fails
            'generate_summary_report': True
        }
        
        # Track audit results
        self.audit_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'panic_kit_id': f"panic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'audits_run': [],
            'total_audits': 0,
            'successful_audits': 0,
            'failed_audits': 0,
            'critical_findings': [],
            'warning_findings': [],
            'overall_status': 'unknown',
            'duration_seconds': 0,
            'exit_code': 0
        }
        
        # Define audit sequence
        self.audit_sequence = [
            {
                'name': 'Monthly Deep Audit',
                'command': [sys.executable, 'audit/monthly_audit.py', '--run'],
                'timeout': 600,
                'critical': True,
                'description': 'Comprehensive data integrity, sync consistency, and backup verification'
            },
            {
                'name': 'Restore Verification',
                'command': [sys.executable, 'audit/verify_restore.py', '--run'],
                'timeout': 900,
                'critical': True,
                'description': 'Dry-run restore validation and backup integrity checking'
            },
            {
                'name': 'Performance Benchmark',
                'command': [sys.executable, 'perf/perf_benchmark.py', '--run'],
                'timeout': 300,
                'critical': False,
                'description': 'Performance monitoring across Supabase, Notion, and Git operations'
            },
            {
                'name': 'Operational Smoke Tests',
                'command': [sys.executable, 'operational_smoke_tests.py', '--run'],
                'timeout': 300,
                'critical': True,
                'description': 'Comprehensive operational validation and health verification'
            }
        ]
        
        self.logger.info("🚨 Angles AI Universe™ Panic Kit Audit Runner Initialized")
    
    def setup_logging(self):
        """Setup logging for panic kit"""
        os.makedirs("logs/audit", exist_ok=True)
        
        self.logger = logging.getLogger('panic_kit')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/audit/panic_kit.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def run_single_audit(self, audit_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single audit with comprehensive error handling"""
        audit_name = audit_config['name']
        self.logger.info(f"🔍 Running {audit_name}...")
        
        audit_result = {
            'name': audit_name,
            'command': ' '.join(audit_config['command']),
            'success': False,
            'duration': 0,
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'critical_issues': [],
            'warning_issues': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        start_time = time.time()
        
        try:
            # Execute audit command
            process = subprocess.run(
                audit_config['command'],
                capture_output=True,
                text=True,
                timeout=audit_config['timeout']
            )
            
            audit_result['returncode'] = process.returncode
            audit_result['stdout'] = process.stdout
            audit_result['stderr'] = process.stderr
            audit_result['success'] = process.returncode == 0
            
            duration = time.time() - start_time
            audit_result['duration'] = duration
            
            # Parse output for findings
            self.parse_audit_output(audit_result)
            
            status_icon = "✅" if audit_result['success'] else "❌"
            self.logger.info(f"{status_icon} {audit_name} completed in {duration:.1f}s (exit: {process.returncode})")
            
            # Log summary of findings
            if audit_result['critical_issues']:
                self.logger.error(f"🚨 {audit_name}: {len(audit_result['critical_issues'])} critical issues found")
                for issue in audit_result['critical_issues']:
                    self.logger.error(f"   • {issue}")
            
            if audit_result['warning_issues']:
                self.logger.warning(f"⚠️ {audit_name}: {len(audit_result['warning_issues'])} warnings found")
                for warning in audit_result['warning_issues']:
                    self.logger.warning(f"   • {warning}")
            
            if audit_result['success'] and not audit_result['critical_issues']:
                self.logger.info(f"✅ {audit_name}: All checks passed")
        
        except subprocess.TimeoutExpired:
            audit_result['stderr'] = f"Audit timed out after {audit_config['timeout']} seconds"
            audit_result['critical_issues'].append(f"Audit timeout ({audit_config['timeout']}s)")
            self.logger.error(f"❌ {audit_name} timed out after {audit_config['timeout']}s")
        
        except Exception as e:
            audit_result['stderr'] = f"Audit execution failed: {str(e)}"
            audit_result['critical_issues'].append(f"Execution failure: {str(e)}")
            self.logger.error(f"❌ {audit_name} failed: {str(e)}")
        
        return audit_result
    
    def parse_audit_output(self, audit_result: Dict[str, Any]):
        """Parse audit output for critical findings and warnings"""
        stdout = audit_result['stdout']
        stderr = audit_result['stderr']
        combined_output = f"{stdout}\n{stderr}"
        
        # Look for critical patterns
        critical_patterns = [
            'critical',
            'failed',
            'error',
            'unable to',
            'connection failed',
            'backup missing',
            'integrity violation',
            'sync drift',
            'schema mismatch'
        ]
        
        warning_patterns = [
            'warning',
            'slow',
            'degraded',
            'missing optional',
            'performance issue',
            'stale backup',
            'minor drift'
        ]
        
        # Extract critical issues
        for line in combined_output.lower().split('\n'):
            line = line.strip()
            if any(pattern in line for pattern in critical_patterns):
                if not any(pattern in line for pattern in ['warning', 'minor', 'optional']):
                    audit_result['critical_issues'].append(line[:200])  # Truncate long lines
        
        # Extract warnings
        for line in combined_output.lower().split('\n'):
            line = line.strip()
            if any(pattern in line for pattern in warning_patterns):
                if not any(pattern in line for pattern in critical_patterns):
                    audit_result['warning_issues'].append(line[:200])  # Truncate long lines
        
        # Remove duplicates
        audit_result['critical_issues'] = list(set(audit_result['critical_issues']))
        audit_result['warning_issues'] = list(set(audit_result['warning_issues']))
    
    def generate_panic_report(self) -> str:
        """Generate comprehensive panic kit report"""
        report_content = f"""# Panic Kit Audit Report

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Panic Kit ID:** {self.audit_results['panic_kit_id']}  
**Overall Status:** {self.audit_results['overall_status']}  
**Total Duration:** {self.audit_results['duration_seconds']:.1f} seconds

## Executive Summary

- **Total Audits:** {self.audit_results['total_audits']}
- **Successful:** {self.audit_results['successful_audits']}
- **Failed:** {self.audit_results['failed_audits']}
- **Critical Findings:** {len(self.audit_results['critical_findings'])}
- **Warning Findings:** {len(self.audit_results['warning_findings'])}

## Audit Results

"""
        
        for audit in self.audit_results['audits_run']:
            status_icon = "✅" if audit['success'] else "❌"
            report_content += f"### {status_icon} {audit['name']}\n\n"
            report_content += f"**Duration:** {audit['duration']:.1f}s  \n"
            report_content += f"**Exit Code:** {audit['returncode']}  \n"
            
            if audit['critical_issues']:
                report_content += f"**Critical Issues:** {len(audit['critical_issues'])}  \n"
                for issue in audit['critical_issues']:
                    report_content += f"- 🚨 {issue}\n"
                report_content += "\n"
            
            if audit['warning_issues']:
                report_content += f"**Warnings:** {len(audit['warning_issues'])}  \n"
                for warning in audit['warning_issues']:
                    report_content += f"- ⚠️ {warning}\n"
                report_content += "\n"
            
            if audit['success'] and not audit['critical_issues']:
                report_content += "**Status:** All checks passed ✅\n\n"
        
        if self.audit_results['critical_findings']:
            report_content += "## Critical Findings Summary\n\n"
            for finding in self.audit_results['critical_findings']:
                report_content += f"- 🚨 {finding}\n"
            report_content += "\n"
        
        if self.audit_results['warning_findings']:
            report_content += "## Warning Findings Summary\n\n"
            for finding in self.audit_results['warning_findings']:
                report_content += f"- ⚠️ {finding}\n"
            report_content += "\n"
        
        report_content += f"""## Recommendations

{'🚨 **IMMEDIATE ACTION REQUIRED** - Critical issues detected that require urgent attention.' if self.audit_results['critical_findings'] else ''}
{'⚠️ **ATTENTION NEEDED** - Warning issues detected that should be addressed.' if self.audit_results['warning_findings'] and not self.audit_results['critical_findings'] else ''}
{'✅ **SYSTEM HEALTHY** - All audits passed successfully.' if not self.audit_results['critical_findings'] and not self.audit_results['warning_findings'] else ''}

## Next Steps

1. **Review Critical Issues:** Address all critical findings immediately
2. **Monitor Warnings:** Plan resolution for warning-level issues
3. **Schedule Follow-up:** Re-run panic kit after fixes to verify resolution
4. **Update Documentation:** Record any configuration changes made

---
*Generated by Angles AI Universe™ Panic Kit Audit System*
"""
        
        return report_content
    
    def save_reports(self) -> Dict[str, Optional[str]]:
        """Save JSON and Markdown reports"""
        reports: Dict[str, Optional[str]] = {'json': None, 'markdown': None}
        
        try:
            # Save JSON report
            json_file = f"export/audit/panic_kit_{self.audit_results['panic_kit_id']}.json"
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            
            with open(json_file, 'w') as f:
                json.dump(self.audit_results, f, indent=2)
            
            reports['json'] = json_file
            self.logger.info(f"📄 JSON report saved: {json_file}")
            
            # Save Markdown report
            markdown_file = f"export/audit/panic_kit_{self.audit_results['panic_kit_id']}.md"
            markdown_content = self.generate_panic_report()
            
            with open(markdown_file, 'w') as f:
                f.write(markdown_content)
            
            reports['markdown'] = markdown_file
            self.logger.info(f"📄 Markdown report saved: {markdown_file}")
        
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {str(e)}")
        
        return reports
    
    def send_critical_alerts(self):
        """Send alerts for critical findings"""
        if not self.alert_manager or not self.audit_results['critical_findings']:
            return
        
        try:
            critical_count = len(self.audit_results['critical_findings'])
            failed_audits = self.audit_results['failed_audits']
            
            alert_message = f"Panic Kit detected {critical_count} critical findings across {failed_audits} failed audits. Immediate attention required."
            
            if self.audit_results['critical_findings']:
                alert_message += f"\n\nCritical Issues:\n"
                for finding in self.audit_results['critical_findings'][:5]:  # Limit to 5 for brevity
                    alert_message += f"• {finding}\n"
                
                if len(self.audit_results['critical_findings']) > 5:
                    alert_message += f"• ... and {len(self.audit_results['critical_findings']) - 5} more"
            
            self.alert_manager.send_alert(
                title="🚨 Panic Kit Critical Findings Detected",
                message=alert_message,
                severity="critical",
                tags=['panic-kit', 'critical', 'audit', 'emergency']
            )
            
            self.logger.info("🚨 Critical alert sent via notification system")
        
        except Exception as e:
            self.logger.error(f"❌ Alert sending failed: {str(e)}")
    
    def run_panic_audit_sequence(self) -> int:
        """Run complete panic audit sequence"""
        self.logger.info("🚨 STARTING PANIC KIT EMERGENCY AUDIT SEQUENCE")
        self.logger.info("=" * 80)
        self.logger.info("🔍 Running all available audits to validate system integrity")
        self.logger.info("⚠️ Critical findings will result in non-zero exit code")
        self.logger.info("=" * 80)
        
        total_start_time = time.time()
        
        try:
            # Run each audit in sequence
            for i, audit_config in enumerate(self.audit_sequence, 1):
                self.logger.info(f"\n📋 AUDIT {i}/{len(self.audit_sequence)}: {audit_config['name']}")
                self.logger.info(f"   {audit_config['description']}")
                self.logger.info("-" * 60)
                
                audit_result = self.run_single_audit(audit_config)
                self.audit_results['audits_run'].append(audit_result)
                self.audit_results['total_audits'] += 1
                
                if audit_result['success']:
                    self.audit_results['successful_audits'] += 1
                else:
                    self.audit_results['failed_audits'] += 1
                
                # Aggregate findings
                self.audit_results['critical_findings'].extend(audit_result['critical_issues'])
                self.audit_results['warning_findings'].extend(audit_result['warning_issues'])
                
                # Check if we should stop on critical failure
                if audit_config.get('critical', False) and audit_result['critical_issues']:
                    if not self.config['continue_on_failure']:
                        self.logger.error(f"🛑 Stopping due to critical failure in {audit_config['name']}")
                        break
                    else:
                        self.logger.warning(f"⚠️ Continuing despite critical issues in {audit_config['name']}")
            
            # Calculate final status
            total_duration = time.time() - total_start_time
            self.audit_results['duration_seconds'] = total_duration
            
            critical_count = len(self.audit_results['critical_findings'])
            warning_count = len(self.audit_results['warning_findings'])
            
            if critical_count >= self.config['critical_threshold']:
                self.audit_results['overall_status'] = 'critical'
                self.audit_results['exit_code'] = 2
            elif self.audit_results['failed_audits'] > 0:
                self.audit_results['overall_status'] = 'failed'
                self.audit_results['exit_code'] = 1
            elif warning_count > 0:
                self.audit_results['overall_status'] = 'warning'
                self.audit_results['exit_code'] = 0
            else:
                self.audit_results['overall_status'] = 'healthy'
                self.audit_results['exit_code'] = 0
            
            # Generate reports
            if self.config['generate_summary_report']:
                reports = self.save_reports()
            
            # Send critical alerts
            self.send_critical_alerts()
            
            # Final summary
            self.logger.info("\n" + "=" * 80)
            self.logger.info("🏁 PANIC KIT AUDIT SEQUENCE COMPLETE")
            self.logger.info("=" * 80)
            self.logger.info(f"📊 SUMMARY:")
            self.logger.info(f"   Overall Status: {self.audit_results['overall_status'].upper()}")
            self.logger.info(f"   Total Duration: {total_duration:.1f} seconds")
            self.logger.info(f"   Audits Run: {self.audit_results['total_audits']}")
            self.logger.info(f"   Successful: {self.audit_results['successful_audits']}")
            self.logger.info(f"   Failed: {self.audit_results['failed_audits']}")
            self.logger.info(f"   Critical Findings: {critical_count}")
            self.logger.info(f"   Warning Findings: {warning_count}")
            self.logger.info(f"   Exit Code: {self.audit_results['exit_code']}")
            
            if critical_count > 0:
                self.logger.error("🚨 CRITICAL ISSUES DETECTED - IMMEDIATE ACTION REQUIRED")
                for finding in self.audit_results['critical_findings'][:5]:
                    self.logger.error(f"   • {finding}")
                if critical_count > 5:
                    self.logger.error(f"   • ... and {critical_count - 5} more critical issues")
            elif warning_count > 0:
                self.logger.warning("⚠️ WARNING ISSUES DETECTED - ATTENTION NEEDED")
            else:
                self.logger.info("✅ ALL AUDITS PASSED - SYSTEM HEALTHY")
            
            self.logger.info("=" * 80)
            
            return self.audit_results['exit_code']
        
        except KeyboardInterrupt:
            self.logger.error("🛑 Panic kit interrupted by user")
            return 130  # Standard exit code for SIGINT
        
        except Exception as e:
            self.logger.error(f"💥 Panic kit system failure: {str(e)}")
            return 255  # General system error

def main():
    """Main entry point for panic kit"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Panic Kit - Emergency audit runner')
    parser.add_argument('--run', action='store_true', help='Run complete panic audit sequence')
    parser.add_argument('--list', action='store_true', help='List available audits')
    parser.add_argument('--continue-on-failure', action='store_true', help='Continue even if critical audits fail')
    parser.add_argument('--no-alerts', action='store_true', help='Disable alert notifications')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout per audit in seconds')
    
    args = parser.parse_args()
    
    try:
        panic_kit = PanicKitAuditRunner()
        
        # Override configuration based on args
        if args.continue_on_failure:
            panic_kit.config['continue_on_failure'] = True
        if args.no_alerts:
            panic_kit.alert_manager = None
        if args.timeout:
            for audit in panic_kit.audit_sequence:
                audit['timeout'] = args.timeout
        
        if args.list:
            print("\n🚨 Available Panic Kit Audits:")
            for i, audit in enumerate(panic_kit.audit_sequence, 1):
                critical_marker = "🚨" if audit.get('critical', False) else "ℹ️"
                print(f"  {i}. {critical_marker} {audit['name']}")
                print(f"     {audit['description']}")
                print(f"     Timeout: {audit['timeout']}s")
            print()
        
        elif args.run:
            exit_code = panic_kit.run_panic_audit_sequence()
            sys.exit(exit_code)
        
        else:
            # Default: run panic audit sequence
            exit_code = panic_kit.run_panic_audit_sequence()
            sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print("\n🛑 Panic kit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Panic kit system failure: {str(e)}")
        sys.exit(255)

if __name__ == "__main__":
    main()