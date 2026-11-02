"""
Enhanced monitoring with database integration
"""
import time
from pathlib import Path
from datetime import datetime
from collections import deque
import yaml

from .parser import LogParser
from .predictor import IncidentPredictor
from .db.manager import IncidentDatabase
from .similarity import SimilarityMatcher


class LogMonitor:
    """Monitors logs and stores incidents in database"""
    
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.parser = LogParser(config_path)
        self.predictor = IncidentPredictor(config_path)
        self.db = IncidentDatabase(config_path)
        
        # Circular buffer for context (last 10 logs)
        self.log_buffer = deque(maxlen=10)
        
        # Track last position in log file
        self.last_position = 0
        self.log_file = Path(self.config['logging']['app_log_file'])
        self.similarity_matcher = SimilarityMatcher(config_path)
    
    def read_new_logs(self):
        """
        Read only new log entries since last check
        
        Returns:
            List of new log entries (dicts)
        """
        if not self.log_file.exists():
            return []
        
        new_entries = []
        
        with open(self.log_file, 'r') as f:
            # Seek to last position
            f.seek(self.last_position)
            
            # Read new lines
            for line in f:
                match = self.parser.pattern.match(line.strip())
                if match:
                    entry = match.groupdict()
                    entry['raw_line'] = line.strip()
                    new_entries.append(entry)
            
            # Update position
            self.last_position = f.tell()
        
        return new_entries
    
    def check_for_incidents(self, logs):
        """
        Check logs for incidents using ML classifier
        
        Args:
            logs: List of log dicts
            
        Returns:
            List of incidents detected
        """
        incidents = []
        
        for log in logs:
            # Only check WARN and ERROR logs
            if log['level'] in ['WARN', 'ERROR']:
                # Classify
                prediction = self.predictor.predict(log['message'])
                
                # Skip if classified as "Normal"
                if prediction['incident_type'] != 'Normal':
                    incidents.append({
                        'log': log,
                        'prediction': prediction
                    })
        
        return incidents
    
    def get_context(self, current_index, logs):
        """
        Get context logs (before and after)
        
        Args:
            current_index: Index of current log
            logs: All logs in buffer
            
        Returns:
            Tuple of (before_logs, after_logs)
        """
        before = list(self.log_buffer)[-5:] if len(self.log_buffer) > 0 else []
        after = logs[current_index+1:current_index+6] if current_index < len(logs)-1 else []
        
        return before, after
    
    def monitor_once(self):
        """
        Single monitoring cycle - check for new logs and incidents
        
        Returns:
            Number of incidents detected
        """
        # Read new logs
        new_logs = self.read_new_logs()
        
        if not new_logs:
            return 0
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Read {len(new_logs)} new logs")
        
        # Check for incidents
        incidents_detected = self.check_for_incidents(new_logs)
        
        # Store incidents in database
        for incident_data in incidents_detected:
            log = incident_data['log']
            prediction = incident_data['prediction']

        if is_new:
            # Find similar incidents
            similar = self.similarity_matcher.get_similar_with_context(log['message'])
    
            if similar:
                print(f"   📊 Similar incidents found:")

            for s in similar[:3]:
                inc = s['incident']
                days_ago = (datetime.now() - datetime.fromisoformat(inc['last_seen'])).days
                print(f"      #{inc['id']} - {days_ago} days ago ({s['similarity']:.0%} similar)")
                if s['resolution']:
                    print(f"         Fixed: {s['resolution']['notes']}")
            
            # Get context
            idx = new_logs.index(log)
            before, after = self.get_context(idx, new_logs)
            
            # Store in database
            incident, occurrence, is_new = self.db.store_incident(
                incident_type=prediction['incident_type'],
                severity=log['level'],
                message=log['message'],
                timestamp=datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S'),
                context_before=before,
                context_after=after
            )
            
            # Log to console
            status = "🆕 NEW" if is_new else "🔄 RECURRING"
            print(f"{status} Incident #{incident.id}: {incident.incident_type}")
            print(f"   Message: {log['message']}")
            print(f"   Confidence: {prediction['confidence']:.1%}")
            print(f"   Total occurrences: {incident.occurrence_count}")
            print()
        
        # Update buffer
        for log in new_logs:
            self.log_buffer.append(log)
        
        return len(incidents_detected)
    
    def monitor_continuous(self, interval=None):
        """
        Continuously monitor logs
        
        Args:
            interval: Check interval in seconds (default: from config)
        """
        if interval is None:
            interval = self.config['monitoring']['check_interval_seconds']
        
        print("🔍 Starting continuous monitoring...")
        print(f"   Log file: {self.log_file}")
        print(f"   Check interval: {interval}s")
        print(f"   Database: {self.config['database']['path']}")
        print()
        
        try:
            while True:
                self.monitor_once()
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
            
            # Show summary
            summary = self.db.get_database_summary()
            print("\n📊 Session Summary:")
            print(f"   Total incidents tracked: {summary['total_unique_incidents']}")
            print(f"   Total occurrences: {summary['total_occurrences']}")
            print(f"   Unresolved: {summary['unresolved_occurrences']}")


if __name__ == "__main__":
    monitor = LogMonitor()
    monitor.monitor_continuous()