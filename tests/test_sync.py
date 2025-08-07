#!/usr/bin/env python3
"""
Integration tests for Supabase-Notion bidirectional sync
Minimal testing with dry-run mode for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sync.config import get_config
from sync.diff import DiffEngine
from sync.run_sync import BidirectionalSync


class TestSyncIntegration(unittest.TestCase):
    """Integration tests for sync service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.diff_engine = DiffEngine()
        
        # Sample test data
        self.sample_supabase_record = {
            'id': 'test-uuid-123',
            'decision': 'Implement user authentication',
            'type': 'Architecture',
            'date': '2025-08-07',
            'created_at': '2025-08-07T10:00:00Z',
            'updated_at': '2025-08-07T10:00:00Z',
            'notion_page_id': None,
            'notion_synced': False,
            'checksum': None
        }
        
        self.sample_notion_record = {
            'notion_page_id': 'notion-page-456',
            'decision': 'Setup CI/CD pipeline',
            'type': 'Ops',
            'date': '2025-08-07',
            'created_at': '2025-08-07T11:00:00Z',
            'updated_at': '2025-08-07T11:00:00Z',
            'checksum': None
        }
    
    def test_checksum_computation(self):
        """Test checksum computation consistency"""
        
        # Test basic checksum
        checksum1 = self.diff_engine.compute_checksum(self.sample_supabase_record)
        checksum2 = self.diff_engine.compute_checksum(self.sample_supabase_record)
        
        self.assertEqual(checksum1, checksum2, "Checksums should be consistent")
        self.assertEqual(len(checksum1), 64, "SHA256 should be 64 characters")
        
        # Test different records produce different checksums
        modified_record = self.sample_supabase_record.copy()
        modified_record['decision'] = 'Different decision'
        
        checksum3 = self.diff_engine.compute_checksum(modified_record)
        self.assertNotEqual(checksum1, checksum3, "Different records should have different checksums")
    
    def test_text_normalization(self):
        """Test text normalization for consistent comparison"""
        
        # Test whitespace normalization
        record1 = {'decision': 'Test   Decision', 'type': 'Policy', 'date': '2025-08-07'}
        record2 = {'decision': 'Test Decision', 'type': 'Policy', 'date': '2025-08-07'}
        
        checksum1 = self.diff_engine.compute_checksum(record1)
        checksum2 = self.diff_engine.compute_checksum(record2)
        
        self.assertEqual(checksum1, checksum2, "Normalized text should produce same checksum")
        
        # Test case insensitive
        record3 = {'decision': 'test decision', 'type': 'policy', 'date': '2025-08-07'}
        checksum3 = self.diff_engine.compute_checksum(record3)
        
        self.assertEqual(checksum1, checksum3, "Case should not affect checksum")
    
    def test_record_validation(self):
        """Test record validation logic"""
        
        # Valid record
        valid_record = {
            'decision': 'Valid decision',
            'type': 'Architecture',
            'date': '2025-08-07'
        }
        self.assertTrue(self.diff_engine.validate_record(valid_record))
        
        # Missing required fields
        invalid_records = [
            {'type': 'Architecture', 'date': '2025-08-07'},  # Missing decision
            {'decision': 'Test', 'date': '2025-08-07'},      # Missing type
            {'decision': 'Test', 'type': 'Architecture'}     # Missing date
        ]
        
        for record in invalid_records:
            self.assertFalse(self.diff_engine.validate_record(record))
    
    def test_sync_delta_computation(self):
        """Test sync delta computation logic"""
        
        # Prepare test data
        supabase_records = [self.sample_supabase_record.copy()]
        notion_records = [self.sample_notion_record.copy()]
        
        # Compute checksums
        for record in supabase_records:
            record['checksum'] = self.diff_engine.compute_checksum(record)
        for record in notion_records:
            record['checksum'] = self.diff_engine.compute_checksum(record)
        
        # Compute delta
        delta = self.diff_engine.compute_sync_delta(supabase_records, notion_records)
        
        # Should create one record in each direction (no matches)
        self.assertEqual(len(delta.create_in_notion), 1, "Should create Supabase record in Notion")
        self.assertEqual(len(delta.create_in_supabase), 1, "Should create Notion record in Supabase")
        self.assertEqual(len(delta.update_in_notion), 0, "No updates needed")
        self.assertEqual(len(delta.update_in_supabase), 0, "No updates needed")
    
    def test_matching_by_checksum(self):
        """Test record matching by checksum"""
        
        # Create matching records with same content but different IDs
        sb_record = self.sample_supabase_record.copy()
        notion_record = self.sample_notion_record.copy()
        
        # Make them have same content
        notion_record.update({
            'decision': sb_record['decision'],
            'type': sb_record['type'],
            'date': sb_record['date']
        })
        
        # Compute checksums
        sb_record['checksum'] = self.diff_engine.compute_checksum(sb_record)
        notion_record['checksum'] = self.diff_engine.compute_checksum(notion_record)
        
        # They should have the same checksum now
        self.assertEqual(sb_record['checksum'], notion_record['checksum'])
        
        # Compute delta
        delta = self.diff_engine.compute_sync_delta([sb_record], [notion_record])
        
        # Should match by checksum and link them
        self.assertEqual(len(delta.create_in_notion), 0, "No creates needed")
        self.assertEqual(len(delta.create_in_supabase), 0, "No creates needed")
        self.assertEqual(len(delta.update_in_supabase), 1, "Should update Supabase with notion_page_id")
    
    def test_dry_run_sync(self):
        """Test dry-run sync operation"""
        
        try:
            # This requires valid environment variables
            sync_runner = BidirectionalSync(dry_run=True)
            
            # Should not raise exception and not make any changes
            result = sync_runner.run_sync()
            
            # Verify it's marked as dry run
            self.assertIsNotNone(result, "Dry run should return results")
            self.assertIsInstance(result, dict, "Results should be a dictionary")
            
            print("✅ Dry-run sync test passed")
            
        except Exception as e:
            # If environment not set up, skip this test
            if "Missing required environment variables" in str(e):
                self.skipTest(f"Environment not configured: {e}")
            else:
                raise
    
    def test_config_loading(self):
        """Test configuration loading"""
        
        try:
            config = get_config()
            
            # Verify required fields are present
            self.assertIsNotNone(config.supabase_url)
            self.assertIsNotNone(config.supabase_service_key)
            self.assertIsNotNone(config.notion_api_key)
            self.assertIsNotNone(config.notion_database_id)
            
            # Verify defaults
            self.assertEqual(config.batch_size, 100)
            self.assertEqual(config.max_retries, 3)
            self.assertEqual(config.sync_interval, 15)
            
            print("✅ Configuration test passed")
            
        except ValueError as e:
            if "Missing required environment variables" in str(e):
                self.skipTest(f"Environment not configured: {e}")
            else:
                raise


def run_integration_test():
    """Run integration test manually"""
    
    print("🧪 SUPABASE-NOTION SYNC INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Test configuration
        print("📋 Testing configuration...")
        config = get_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   Batch size: {config.batch_size}")
        print(f"   Sync interval: {config.sync_interval} minutes")
        print()
        
        # Test diff engine
        print("🔢 Testing diff engine...")
        diff_engine = DiffEngine()
        
        test_record = {
            'decision': 'Test decision',
            'type': 'Architecture',
            'date': '2025-08-07'
        }
        
        checksum = diff_engine.compute_checksum(test_record)
        print(f"✅ Checksum computed: {checksum[:16]}...")
        
        is_valid = diff_engine.validate_record(test_record)
        print(f"✅ Record validation: {is_valid}")
        print()
        
        # Test dry-run sync
        print("🔍 Testing dry-run sync...")
        sync_runner = BidirectionalSync(dry_run=True)
        result = sync_runner.run_sync()
        
        print(f"✅ Dry-run completed successfully")
        print(f"   Duration: {result.get('duration', 0):.2f} seconds")
        print(f"   Supabase records: {result.get('supabase_count', 0)}")
        print(f"   Notion records: {result.get('notion_count', 0)}")
        print()
        
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Run integration test if called directly
    success = run_integration_test()
    sys.exit(0 if success else 1)