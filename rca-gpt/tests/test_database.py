"""
Tests for database functionality
"""
import unittest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from rca_gpt.db.manager import IncidentDatabase
from rca_gpt.db.models import Incident, IncidentOccurrence


class TestIncidentDatabase(unittest.TestCase):
    
    def setUp(self):
        """Create temporary database for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = {
            'database': {'path': str(Path(self.temp_dir) / 'test.db')},
            'monitoring': {'check_interval_seconds': 60}
        }
        
        # Create temp config file
        self.config_file = Path(self.temp_dir) / 'config.yaml'
        import yaml
        with open(self.config_file, 'w') as f:
            yaml.dump(self.test_config, f)
        
        self.db = IncidentDatabase(str(self.config_file))
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_store_new_incident(self):
        """Test storing a new incident"""
        incident, occurrence, is_new = self.db.store_incident(
            incident_type='Auth Error',
            severity='ERROR',
            message='Invalid token',
            timestamp=datetime.utcnow()
        )
        
        self.assertTrue(is_new)
        self.assertIsNotNone(incident.id)
        self.assertEqual(incident.incident_type, 'Auth Error')
        self.assertEqual(incident.occurrence_count, 1)
    
    def test_store_duplicate_incident(self):
        """Test that duplicate incidents update existing record"""
        # First occurrence
        incident1, _, is_new1 = self.db.store_incident(
            incident_type='Auth Error',
            severity='ERROR',
            message='Invalid token'
        )
        
        # Second occurrence (same fingerprint)
        incident2, _, is_new2 = self.db.store_incident(
            incident_type='Auth Error',
            severity='ERROR',
            message='Invalid token'
        )
        
        self.assertTrue(is_new1)
        self.assertFalse(is_new2)
        self.assertEqual(incident1.id, incident2.id)
        self.assertEqual(incident2.occurrence_count, 2)
    
    def test_fingerprint_generation(self):
        """Test fingerprint uniqueness"""
        fp1 = IncidentDatabase.generate_fingerprint('Auth Error', 'Invalid token')
        fp2 = IncidentDatabase.generate_fingerprint('Auth Error', 'Invalid token')
        fp3 = IncidentDatabase.generate_fingerprint('Auth Error', 'Connection timeout')
        
        # Same input = same fingerprint
        self.assertEqual(fp1, fp2)
        
        # Different input = different fingerprint
        self.assertNotEqual(fp1, fp3)
    
    def test_get_recent_incidents(self):
        """Test retrieving recent incidents"""
        # Store some incidents
        for i in range(5):
            self.db.store_incident(
                incident_type='Test Error',
                severity='ERROR',
                message=f'Test message {i}'
            )
        
        incidents = self.db.get_recent_incidents(limit=3)
        self.assertEqual(len(incidents), 3)
    
    def test_incident_stats(self):
        """Test statistics calculation"""
        # Store different types
        self.db.store_incident('Auth Error', 'ERROR', 'Invalid token')
        self.db.store_incident('Auth Error', 'ERROR', 'Invalid token')  # duplicate
        self.db.store_incident('Timeout', 'WARN', 'Request timeout')
        
        stats = self.db.get_incident_stats(days=1)
        
        self.assertIn('Auth Error', stats)
        self.assertIn('Timeout', stats)
        self.assertEqual(stats['Auth Error']['total_occurrences'], 2)
        self.assertEqual(stats['Timeout']['total_occurrences'], 1)
    
    def test_mark_resolved(self):
        """Test marking incidents as resolved"""
        _, occurrence, _ = self.db.store_incident(
            'Test Error', 'ERROR', 'Test message'
        )
        
        # Mark as resolved
        updated = self.db.mark_resolved(
            occurrence.id,
            resolution_notes='Restarted service',
            resolved_by='test_user'
        )
        
        self.assertTrue(updated.resolved)
        self.assertEqual(updated.resolution_notes, 'Restarted service')
        self.assertEqual(updated.resolved_by, 'test_user')
        self.assertIsNotNone(updated.resolved_at)
    
    def test_search_incidents(self):
        """Test incident search"""
        self.db.store_incident('Auth Error', 'ERROR', 'Invalid token')
        self.db.store_incident('Timeout', 'WARN', 'Connection timeout')
        self.db.store_incident('DB Error', 'ERROR', 'Connection refused')
        
        # Search for 'connection'
        results = self.db.search_incidents('connection')
        self.assertEqual(len(results), 2)  # timeout and connection refused
    
    def test_context_storage(self):
        """Test storing context logs"""
        context_before = [
            {'level': 'INFO', 'message': 'Starting process'},
            {'level': 'INFO', 'message': 'Loading config'}
        ]
        context_after = [
            {'level': 'ERROR', 'message': 'Process failed'},
        ]
        
        _, occurrence, _ = self.db.store_incident(
            'Test Error',
            'ERROR',
            'Main error',
            context_before=context_before,
            context_after=context_after
        )
        
        retrieved_before = occurrence.get_context_before()
        retrieved_after = occurrence.get_context_after()
        
        self.assertEqual(len(retrieved_before), 2)
        self.assertEqual(len(retrieved_after), 1)
        self.assertEqual(retrieved_before[0]['message'], 'Starting process')


if __name__ == '__main__':
    unittest.main()