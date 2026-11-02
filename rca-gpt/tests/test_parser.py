"""
Basic tests for log parser
"""
import unittest
from pathlib import Path
import tempfile
from rca_gpt.parser import LogParser


class TestLogParser(unittest.TestCase):
    
    def setUp(self):
        """Create temporary log file for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test.log"
        
        # Write test logs
        with open(self.log_file, 'w') as f:
            f.write("[INFO] 2025-01-01 10:00:00 - Login success\n")
            f.write("[ERROR] 2025-01-01 10:00:05 - Invalid token\n")
            f.write("[WARN] 2025-01-01 10:00:10 - Connection refused\n")
    
    def test_parse_valid_logs(self):
        """Test parsing valid log entries"""
        parser = LogParser()
        df = parser.parse_log_file(self.log_file)
        
        self.assertEqual(len(df), 3)
        self.assertIn('level', df.columns)
        self.assertIn('timestamp', df.columns)
        self.assertIn('message', df.columns)
    
    def test_log_levels(self):
        """Test that log levels are correctly extracted"""
        parser = LogParser()
        df = parser.parse_log_file(self.log_file)
        
        levels = df['level'].tolist()
        self.assertIn('INFO', levels)
        self.assertIn('ERROR', levels)
        self.assertIn('WARN', levels)
    
    def test_messages(self):
        """Test that messages are correctly extracted"""
        parser = LogParser()
        df = parser.parse_log_file(self.log_file)
        
        messages = df['message'].tolist()
        self.assertIn('Login success', messages)
        self.assertIn('Invalid token', messages)


if __name__ == '__main__':
    unittest.main()