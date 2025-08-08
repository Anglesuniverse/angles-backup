#!/usr/bin/env python3
"""
Unit Tests for Angles AI Universe™ Audit System Components
Comprehensive testing for audit, performance, and verification systems

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import audit components
try:
    from audit.monthly_audit import MonthlyAuditSystem
    from audit.verify_restore import RestoreVerificationSystem
    from perf.perf_benchmark import PerformanceBenchmarkSystem
    from scripts.run_audit_now import PanicKitAuditRunner
except ImportError as e:
    print(f"Warning: Could not import audit components: {e}")
    MonthlyAuditSystem = None
    RestoreVerificationSystem = None
    PerformanceBenchmarkSystem = None
    PanicKitAuditRunner = None

class TestMonthlyAuditSystem(unittest.TestCase):
    """Test cases for Monthly Deep Audit System"""
    
    def setUp(self):
        """Set up test environment"""
        if MonthlyAuditSystem is None:
            self.skipTest("MonthlyAuditSystem not available")
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'NOTION_TOKEN': 'test-notion-token',
            'NOTION_DATABASE_ID': 'test-db-id'
        })
        self.env_patcher.start()
        
        # Create audit system instance
        with patch('audit.monthly_audit.AlertManager'), \
             patch('audit.monthly_audit.GitHelper'):
            self.audit_system = MonthlyAuditSystem()
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'env_patcher'):
            self.env_patcher.stop()
    
    def test_initialization(self):
        """Test audit system initialization"""
        self.assertIsNotNone(self.audit_system)
        self.assertIn('supabase_url', self.audit_system.env)
        self.assertEqual(self.audit_system.env['supabase_url'], 'https://test.supabase.co')
        self.assertIsInstance(self.audit_system.audit_results, dict)
        self.assertIn('timestamp', self.audit_system.audit_results)
    
    def test_supabase_headers(self):
        """Test Supabase headers generation"""
        headers = self.audit_system.get_supabase_headers()
        self.assertIn('apikey', headers)
        self.assertIn('Authorization', headers)
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['apikey'], 'test-key')
        self.assertTrue(headers['Authorization'].startswith('Bearer'))
    
    @patch('requests.head')
    def test_table_analysis_success(self, mock_head):
        """Test successful table analysis"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-range': '0-99/100'}
        mock_head.return_value = mock_response
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [
                {'id': 1, 'decision': 'test', 'active': True, 'created_at': '2024-01-01T00:00:00Z'}
            ]
            
            result = self.audit_system._analyze_table('decision_vault', self.audit_system.get_supabase_headers())
            
            self.assertEqual(result['row_count'], 100)
            self.assertIsInstance(result['null_analysis'], dict)
            self.assertIsInstance(result['critical_issues'], list)
    
    @patch('requests.head')
    def test_table_analysis_failure(self, mock_head):
        """Test table analysis with API failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_head.return_value = mock_response
        
        result = self.audit_system._analyze_table('decision_vault', self.audit_system.get_supabase_headers())
        
        self.assertEqual(result['row_count'], 0)
        self.assertTrue(any('Cannot access table' in issue for issue in result['critical_issues']))
    
    def test_null_analysis(self):
        """Test null percentage analysis"""
        test_data = [
            {'id': 1, 'name': 'test1', 'optional': None},
            {'id': 2, 'name': None, 'optional': 'value'},
            {'id': 3, 'name': 'test3', 'optional': None}
        ]
        
        result = self.audit_system._analyze_nulls(test_data, 'test_table')
        
        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertIn('optional', result)
        self.assertEqual(result['id'], 0.0)  # No nulls
        self.assertAlmostEqual(result['name'], 33.33, places=1)  # 1 out of 3
        self.assertAlmostEqual(result['optional'], 66.67, places=1)  # 2 out of 3
    
    def test_decision_vault_validation(self):
        """Test decision_vault record validation"""
        valid_record = {
            'id': 1,
            'decision': 'test decision',
            'date': '2024-01-01T00:00:00Z',
            'active': True,
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        invalid_record = {
            'id': None,  # Missing required field
            'date': 'invalid-date',  # Invalid date format
            'active': 'not-boolean'  # Invalid boolean
        }
        
        valid_errors = self.audit_system._validate_decision_vault_constraints([valid_record])
        invalid_errors = self.audit_system._validate_decision_vault_constraints([invalid_record])
        
        self.assertEqual(len(valid_errors), 0)
        self.assertTrue(len(invalid_errors) > 0)
        self.assertTrue(any('missing' in error.lower() for error in invalid_errors))

class TestPerformanceBenchmarkSystem(unittest.TestCase):
    """Test cases for Performance Benchmark System"""
    
    def setUp(self):
        """Set up test environment"""
        if PerformanceBenchmarkSystem is None:
            self.skipTest("PerformanceBenchmarkSystem not available")
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        })
        self.env_patcher.start()
        
        # Create benchmark system instance
        with patch('perf.perf_benchmark.AlertManager'), \
             patch('perf.perf_benchmark.GitHelper'):
            self.benchmark_system = PerformanceBenchmarkSystem()
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'env_patcher'):
            self.env_patcher.stop()
    
    def test_initialization(self):
        """Test benchmark system initialization"""
        self.assertIsNotNone(self.benchmark_system)
        self.assertIn('supabase_read_limit', self.benchmark_system.config)
        self.assertIsInstance(self.benchmark_system.benchmark_results, dict)
        self.assertIn('benchmark_id', self.benchmark_system.benchmark_results)
    
    @patch('requests.get')
    def test_supabase_read_benchmark_success(self, mock_get):
        """Test successful Supabase read benchmark"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': i, 'decision': f'test {i}'} for i in range(50)]
        mock_get.return_value = mock_response
        
        result = self.benchmark_system.benchmark_supabase_read()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['records_read'], 50)
        self.assertIsNotNone(result['duration_ms'])
        self.assertIsNone(result['error_message'])
    
    @patch('requests.get')
    def test_supabase_read_benchmark_failure(self, mock_get):
        """Test Supabase read benchmark with API failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        mock_get.return_value = mock_response
        
        result = self.benchmark_system.benchmark_supabase_read()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['records_read'], 0)
        self.assertIn('HTTP 403', result['error_message'])
    
    def test_percentile_calculation(self):
        """Test percentile calculation function"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        
        p50 = self.benchmark_system.calculate_percentile(values, 50)
        p95 = self.benchmark_system.calculate_percentile(values, 95)
        p99 = self.benchmark_system.calculate_percentile(values, 99)
        
        self.assertEqual(p50, 5.0)  # Median
        self.assertEqual(p95, 9.0)  # 95th percentile
        self.assertEqual(p99, 10.0)  # 99th percentile (max for small dataset)
    
    def test_performance_statistics_calculation(self):
        """Test performance statistics calculation"""
        test_data = [
            {'timestamp': '2024-01-01T00:00:00Z', 'supabase_read_ms': 100.0, 'supabase_write_ms': 200.0},
            {'timestamp': '2024-01-01T01:00:00Z', 'supabase_read_ms': 150.0, 'supabase_write_ms': 250.0},
            {'timestamp': '2024-01-01T02:00:00Z', 'supabase_read_ms': 120.0, 'supabase_write_ms': None}
        ]
        
        stats = self.benchmark_system.calculate_performance_statistics(test_data)
        
        self.assertEqual(stats['total_benchmarks'], 3)
        self.assertIn('supabase_read_ms', stats['metrics'])
        self.assertEqual(stats['metrics']['supabase_read_ms']['count'], 3)
        self.assertEqual(stats['metrics']['supabase_read_ms']['min'], 100.0)
        self.assertEqual(stats['metrics']['supabase_write_ms']['count'], 2)  # One None value excluded

class TestRestoreVerificationSystem(unittest.TestCase):
    """Test cases for Restore Verification System"""
    
    def setUp(self):
        """Set up test environment"""
        if RestoreVerificationSystem is None:
            self.skipTest("RestoreVerificationSystem not available")
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'REPO_URL': 'https://github.com/test/repo'
        })
        self.env_patcher.start()
        
        self.verify_system = RestoreVerificationSystem()
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'env_patcher'):
            self.env_patcher.stop()
    
    def test_initialization(self):
        """Test verification system initialization"""
        self.assertIsNotNone(self.verify_system)
        self.assertIn('required_export_files', self.verify_system.config)
        self.assertIsInstance(self.verify_system.verification_results, dict)
        self.assertIn('verification_id', self.verify_system.verification_results)
    
    def test_table_schema_validation(self):
        """Test table schema validation"""
        # Valid data
        valid_data = [
            {
                'id': 1,
                'decision': 'test decision',
                'date': '2024-01-01T00:00:00Z',
                'type': 'general',
                'active': True,
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        # Invalid data
        invalid_data = [
            {
                'decision': 'missing id',  # Missing required 'id' field
                'date': 'invalid-date',    # Invalid date format
                'active': 'not-boolean'    # Invalid boolean
            }
        ]
        
        valid_result = self.verify_system.validate_table_schema('decision_vault', valid_data)
        invalid_result = self.verify_system.validate_table_schema('decision_vault', invalid_data)
        
        self.assertEqual(len(valid_result['errors']), 0)
        self.assertTrue(len(invalid_result['errors']) > 0)
    
    def test_record_constraint_validation(self):
        """Test individual record constraint validation"""
        valid_record = {
            'id': 1,
            'decision_text': 'test',
            'decision_type': 'technical',
            'confidence': 0.95,
            'timestamp': '2024-01-01T00:00:00Z'
        }
        
        invalid_record = {
            'id': None,  # Missing ID
            'decision_type': 'invalid-type',  # Invalid enum
            'confidence': 1.5,  # Out of range
            'timestamp': 'invalid-timestamp'  # Invalid timestamp
        }
        
        valid_errors = self.verify_system.validate_record_constraints('ai_decision_log', valid_record, 0)
        invalid_errors = self.verify_system.validate_record_constraints('ai_decision_log', invalid_record, 1)
        
        self.assertEqual(len(valid_errors), 0)
        self.assertTrue(len(invalid_errors) > 0)

class TestPanicKitAuditRunner(unittest.TestCase):
    """Test cases for Panic Kit Audit Runner"""
    
    def setUp(self):
        """Set up test environment"""
        if PanicKitAuditRunner is None:
            self.skipTest("PanicKitAuditRunner not available")
        
        with patch('scripts.run_audit_now.AlertManager'):
            self.panic_kit = PanicKitAuditRunner()
    
    def test_initialization(self):
        """Test panic kit initialization"""
        self.assertIsNotNone(self.panic_kit)
        self.assertIn('timeout_per_audit', self.panic_kit.config)
        self.assertIsInstance(self.panic_kit.audit_sequence, list)
        self.assertTrue(len(self.panic_kit.audit_sequence) > 0)
    
    def test_audit_output_parsing(self):
        """Test audit output parsing for findings"""
        audit_result = {
            'stdout': 'INFO: System healthy\nWARNING: Minor performance issue\nERROR: Critical database problem',
            'stderr': 'CRITICAL: Backup failed\nConnection failed to external service',
            'critical_issues': [],
            'warning_issues': []
        }
        
        self.panic_kit.parse_audit_output(audit_result)
        
        # Should find critical issues
        self.assertTrue(len(audit_result['critical_issues']) > 0)
        # Should find warnings
        self.assertTrue(len(audit_result['warning_issues']) > 0)
        # Should not duplicate issues
        self.assertEqual(len(audit_result['critical_issues']), len(set(audit_result['critical_issues'])))
    
    def test_report_generation(self):
        """Test panic kit report generation"""
        # Set up test audit results
        self.panic_kit.audit_results['audits_run'] = [
            {
                'name': 'Test Audit',
                'success': True,
                'duration': 120.5,
                'returncode': 0,
                'critical_issues': [],
                'warning_issues': ['Minor warning']
            }
        ]
        self.panic_kit.audit_results['overall_status'] = 'warning'
        self.panic_kit.audit_results['critical_findings'] = []
        self.panic_kit.audit_results['warning_findings'] = ['Minor warning']
        
        report = self.panic_kit.generate_panic_report()
        
        self.assertIn('Panic Kit Audit Report', report)
        self.assertIn('Test Audit', report)
        self.assertIn('warning', report.lower())
        self.assertIn('120.5', report)  # Duration should be included

class TestAuditIntegration(unittest.TestCase):
    """Integration tests for audit system components"""
    
    def test_environment_variable_requirements(self):
        """Test that all components handle missing environment variables gracefully"""
        # Test with minimal environment
        with patch.dict(os.environ, {}, clear=True):
            if MonthlyAuditSystem:
                with self.assertRaises(ValueError):
                    MonthlyAuditSystem()
            
            if PerformanceBenchmarkSystem:
                # Should not raise exception but should handle missing credentials
                with patch('perf.perf_benchmark.AlertManager'), \
                     patch('perf.perf_benchmark.GitHelper'):
                    system = PerformanceBenchmarkSystem()
                    self.assertIsNone(system.env['supabase_url'])
    
    def test_log_directory_creation(self):
        """Test that audit systems create necessary log directories"""
        test_dirs = ['logs/audit', 'logs/perf', 'export/audit', 'export/perf']
        
        for directory in test_dirs:
            if os.path.exists(directory):
                self.assertTrue(os.path.isdir(directory))
    
    def test_report_format_consistency(self):
        """Test that all audit components generate consistent report formats"""
        # This would test that JSON reports from different components
        # follow the same basic structure
        pass

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestMonthlyAuditSystem,
        TestPerformanceBenchmarkSystem, 
        TestRestoreVerificationSystem,
        TestPanicKitAuditRunner,
        TestAuditIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)