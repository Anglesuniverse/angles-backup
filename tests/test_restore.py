#!/usr/bin/env python3
"""
Unit and Integration Tests for GitHub Restore System
Tests restore functionality with fixtures and mocks

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.json_sanitizer import JSONSanitizer
from utils.git_helpers import GitHelpers
from github_restore import GitHubRestoreSystem

class TestJSONSanitizer(unittest.TestCase):
    """Test JSON sanitization and validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sanitizer = JSONSanitizer()
        
        # Sample valid decision record
        self.valid_record = {
            "id": "test-12345",
            "decision": "Use Python for backend development",
            "date": "2025-08-07",
            "type": "technical",
            "active": True,
            "comment": "Decision made after team discussion",
            "created_at": "2025-08-07T10:00:00Z",
            "updated_at": "2025-08-07T10:00:00Z"
        }
        
        # Sample invalid record
        self.invalid_record = {
            "decision": "Incomplete record",
            # Missing required fields: date, type, active
            "api_key": "secret-key-12345"  # Should be removed
        }
    
    def test_sanitize_data_removes_secrets(self):
        """Test that secret keys are removed during sanitization"""
        data = {
            "decision": "Test decision",
            "api_key": "secret-123",
            "token": "bearer-456",
            "password": "secret-pass",
            "normal_field": "normal-value"
        }
        
        sanitized = self.sanitizer.sanitize_data(data, remove_secrets=True)
        
        self.assertIn("decision", sanitized)
        self.assertIn("normal_field", sanitized)
        self.assertNotIn("api_key", sanitized)
        self.assertNotIn("token", sanitized)
        self.assertNotIn("password", sanitized)
    
    def test_validate_valid_record(self):
        """Test validation of a valid decision record"""
        result = self.sanitizer.validate_decision_vault_record(self.valid_record)
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["record"], self.valid_record)
    
    def test_validate_invalid_record(self):
        """Test validation of an invalid decision record"""
        result = self.sanitizer.validate_decision_vault_record(self.invalid_record)
        
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)
        
        # Check specific errors
        error_messages = " ".join(result["errors"])
        self.assertIn("date", error_messages)
        self.assertIn("type", error_messages)
        self.assertIn("active", error_messages)
    
    def test_create_deterministic_id(self):
        """Test deterministic ID creation"""
        id1 = self.sanitizer.create_deterministic_id(self.valid_record)
        id2 = self.sanitizer.create_deterministic_id(self.valid_record)
        
        self.assertEqual(id1, id2)  # Should be deterministic
        self.assertTrue(len(id1) == 36)  # UUID format
        self.assertIn("-", id1)  # UUID format with dashes
    
    def test_normalize_record(self):
        """Test record normalization"""
        record_without_id = self.valid_record.copy()
        del record_without_id["id"]
        
        normalized = self.sanitizer.normalize_record(record_without_id)
        
        self.assertIn("id", normalized)  # ID should be generated
        self.assertEqual(normalized["decision"], self.valid_record["decision"])
        self.assertEqual(normalized["date"], self.valid_record["date"])

class TestGitHelpers(unittest.TestCase):
    """Test git helper utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.git_helpers = GitHelpers(Path(self.temp_dir))
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token', 'REPO_URL': 'https://github.com/test/repo.git'})
    def test_prepare_repo_url_with_token(self):
        """Test repository URL preparation with token"""
        self.git_helpers.github_token = 'test-token'
        self.git_helpers.repo_url = 'https://github.com/test/repo.git'
        
        url = self.git_helpers._prepare_repo_url_with_token()
        
        self.assertIn('x-access-token:test-token', url)
        self.assertIn('github.com', url)
    
    def test_run_command_success(self):
        """Test successful command execution"""
        result = self.git_helpers._run_command(['echo', 'test'])
        
        self.assertTrue(result['success'])
        self.assertEqual(result['stdout'], 'test')
        self.assertEqual(result['returncode'], 0)
    
    def test_run_command_failure(self):
        """Test failed command execution"""
        result = self.git_helpers._run_command(['false'])  # Command that always fails
        
        self.assertFalse(result['success'])
        self.assertNotEqual(result['returncode'], 0)

class TestGitHubRestoreSystem(unittest.TestCase):
    """Test the main restore system"""
    
    def setUp(self):
        """Set up test fixtures with mocked clients"""
        # Mock environment variables
        self.env_patch = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'GITHUB_TOKEN': 'test-token',
            'REPO_URL': 'https://github.com/test/repo.git',
            'NOTION_TOKEN': 'test-notion-token',
            'NOTION_DATABASE_ID': 'test-db-id'
        })
        self.env_patch.start()
        
        # Create test data directory
        self.temp_dir = tempfile.mkdtemp()
        self.export_dir = Path(self.temp_dir) / 'export'
        self.export_dir.mkdir(exist_ok=True)
        
        # Create sample export file
        self.sample_export = {
            "export_timestamp": "2025-08-07T10:00:00Z",
            "total_decisions": 2,
            "decisions": [
                {
                    "id": "test-1",
                    "decision": "Test decision 1",
                    "date": "2025-08-07",
                    "type": "technical",
                    "active": True,
                    "comment": "Test comment 1"
                },
                {
                    "id": "test-2", 
                    "decision": "Test decision 2",
                    "date": "2025-08-07",
                    "type": "business",
                    "active": True,
                    "comment": "Test comment 2"
                }
            ]
        }
        
        self.export_file = self.export_dir / 'decisions_20250807.json'
        with open(self.export_file, 'w') as f:
            json.dump(self.sample_export, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patch.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('github_restore.create_client')
    @patch('github_restore.NotionClient')
    def test_initialization(self, mock_notion, mock_supabase):
        """Test restore system initialization"""
        mock_supabase.return_value = Mock()
        mock_notion.return_value = Mock()
        
        with patch('github_restore.GitHelpers'), \
             patch('github_restore.JSONSanitizer'):
            restore_system = GitHubRestoreSystem()
            
            self.assertIsNotNone(restore_system.supabase_url)
            self.assertIsNotNone(restore_system.supabase_key)
            self.assertIsNotNone(restore_system.github_token)
    
    def test_find_snapshot_files_explicit(self):
        """Test finding explicit snapshot files"""
        with patch('github_restore.create_client'), \
             patch('github_restore.NotionClient'), \
             patch('github_restore.GitHelpers'), \
             patch('github_restore.JSONSanitizer'):
            
            restore_system = GitHubRestoreSystem()
            
            # Test with explicit files
            result = restore_system.find_snapshot_files(
                explicit_files=[str(self.export_file)]
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(len(result['files']), 1)
            self.assertEqual(result['selection_method'], 'explicit')
    
    def test_find_snapshot_files_auto(self):
        """Test auto-finding snapshot files"""
        with patch('github_restore.create_client'), \
             patch('github_restore.NotionClient'), \
             patch('github_restore.GitHelpers'), \
             patch('github_restore.JSONSanitizer'), \
             patch('pathlib.Path.cwd', return_value=Path(self.temp_dir)):
            
            restore_system = GitHubRestoreSystem()
            
            # Change working directory context
            original_cwd = Path.cwd()
            try:
                os.chdir(self.temp_dir)
                result = restore_system.find_snapshot_files()
                
                self.assertTrue(result['success'])
                self.assertGreater(len(result['files']), 0)
                self.assertEqual(result['selection_method'], 'auto')
            finally:
                os.chdir(original_cwd)
    
    @patch('github_restore.create_client')
    @patch('github_restore.NotionClient')
    def test_dry_run_restore(self, mock_notion, mock_supabase):
        """Test dry-run restore operation"""
        mock_supabase.return_value = Mock()
        mock_notion.return_value = Mock()
        
        with patch('github_restore.GitHelpers') as mock_git, \
             patch('github_restore.JSONSanitizer') as mock_sanitizer:
            
            # Setup mocks
            mock_git.return_value.ensure_repository.return_value = {"success": True}
            mock_git.return_value.safe_pull.return_value = {"success": True}
            
            mock_sanitizer.return_value.validate_json_file.return_value = {
                "success": True,
                "records": self.sample_export["decisions"],
                "total_records": 2,
                "valid_records": 2,
                "invalid_records": 0
            }
            mock_sanitizer.return_value.normalize_record.side_effect = lambda x: x
            
            restore_system = GitHubRestoreSystem()
            
            # Mock the file finding
            with patch.object(restore_system, 'find_snapshot_files') as mock_find:
                mock_find.return_value = {
                    "success": True,
                    "files": [{"path": str(self.export_file), "type": "test", "date": "2025-08-07"}],
                    "selection_method": "test"
                }
                
                result = restore_system.run_restore(dry_run=True)
                
                self.assertTrue(result['success'])
                self.assertTrue(result['dry_run'])
                self.assertGreater(result['records_loaded'], 0)
    
    @patch('github_restore.create_client')
    def test_supabase_restore_idempotency(self, mock_create_client):
        """Test that restore operations are idempotent"""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        mock_create_client.return_value = mock_client
        
        # First restore - no existing records
        mock_table.select.return_value.eq.return_value.execute.return_value.data = []
        mock_table.insert.return_value.execute.return_value.data = [{"id": "test-1"}]
        
        with patch('github_restore.NotionClient'), \
             patch('github_restore.GitHelpers'), \
             patch('github_restore.JSONSanitizer'):
            
            restore_system = GitHubRestoreSystem()
            result1 = restore_system.restore_to_supabase([self.sample_export["decisions"][0]])
            
            self.assertTrue(result1['success'])
            self.assertEqual(result1['inserted'], 1)
            self.assertEqual(result1['updated'], 0)
        
        # Second restore - record exists, should update
        mock_table.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "test-1", "updated_at": "2025-08-07T09:00:00Z"}  # Older timestamp
        ]
        mock_table.update.return_value.eq.return_value.execute.return_value.data = [{"id": "test-1"}]
        
        result2 = restore_system.restore_to_supabase([self.sample_export["decisions"][0]])
        
        self.assertTrue(result2['success'])
        self.assertEqual(result2['inserted'], 0)
        self.assertEqual(result2['updated'], 1)
    
    @patch('github_restore.create_client')
    def test_force_override_newer_records(self, mock_create_client):
        """Test force override of newer records"""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        mock_create_client.return_value = mock_client
        
        # Existing record with newer timestamp
        mock_table.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "test-1", "updated_at": "2025-08-07T12:00:00Z"}  # Newer than our test data
        ]
        mock_table.update.return_value.eq.return_value.execute.return_value.data = [{"id": "test-1"}]
        
        with patch('github_restore.NotionClient'), \
             patch('github_restore.GitHelpers'), \
             patch('github_restore.JSONSanitizer'):
            
            restore_system = GitHubRestoreSystem()
            
            # Without force - should skip
            result1 = restore_system.restore_to_supabase([self.sample_export["decisions"][0]], force=False)
            self.assertEqual(result1['skipped'], 1)
            
            # With force - should update
            result2 = restore_system.restore_to_supabase([self.sample_export["decisions"][0]], force=True)
            self.assertEqual(result2['updated'], 1)

class TestIntegration(unittest.TestCase):
    """Integration tests with real file operations"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)
        
        # Create export directory with test files
        export_dir = Path('export')
        export_dir.mkdir(exist_ok=True)
        
        # Create test export file
        test_data = {
            "export_timestamp": "2025-08-07T10:00:00Z",
            "total_decisions": 1,
            "decisions": [
                {
                    "id": "integration-test-1",
                    "decision": "Integration test decision",
                    "date": "2025-08-07",
                    "type": "technical",
                    "active": True,
                    "comment": "Test for integration"
                }
            ]
        }
        
        with open(export_dir / 'decisions_20250807.json', 'w') as f:
            json.dump(test_data, f)
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_file_validation_integration(self):
        """Test real JSON file validation"""
        sanitizer = JSONSanitizer()
        result = sanitizer.validate_json_file('export/decisions_20250807.json')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total_records'], 1)
        self.assertEqual(result['valid_records'], 1)
        self.assertEqual(len(result['records']), 1)
    
    def test_file_finding_integration(self):
        """Test actual file finding in filesystem"""
        # Mock the dependencies we don't want to test
        with patch('github_restore.create_client'), \
             patch('github_restore.NotionClient'), \
             patch('github_restore.GitHelpers'), \
             patch('github_restore.JSONSanitizer'):
            
            restore_system = GitHubRestoreSystem()
            result = restore_system.find_snapshot_files()
            
            self.assertTrue(result['success'])
            self.assertGreater(len(result['files']), 0)

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestJSONSanitizer))
    suite.addTests(loader.loadTestsFromTestCase(TestGitHelpers))
    suite.addTests(loader.loadTestsFromTestCase(TestGitHubRestoreSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)