"""
Pattern mining - detect incident sequences
"""
from collections import defaultdict, Counter
from datetime import timedelta
from .db.manager import IncidentDatabase


class PatternMiner:
    """Discover recurring incident patterns"""
    
    def __init__(self, config_path='config/config.yaml'):
        self.db = IncidentDatabase(config_path)
    
    def mine_patterns(self, days=30, time_window_minutes=5, min_support=3):
        """
        Find incident sequences that repeat
        
        Args:
            days: Look back period
            time_window_minutes: Max time between incidents in pattern
            min_support: Minimum occurrences to be considered a pattern
            
        Returns:
            List of patterns with metadata
        """
        from datetime import datetime, timedelta
        
        # Get all incidents in time range
        cutoff = datetime.utcnow() - timedelta(days=days)
        incidents = self.db.get_incidents_in_timerange(cutoff)
        
        # Get all occurrences sorted by time
        all_occurrences = []
        for inc in incidents:
            occs = self.db.get_incident_occurrences(inc.id, limit=1000)
            for occ in occs:
                all_occurrences.append({
                    'incident_id': inc.id,
                    'incident_type': inc.incident_type,
                    'timestamp': occ.timestamp,
                    'occurrence_id': occ.id
                })
        
        # Sort by timestamp
        all_occurrences.sort(key=lambda x: x['timestamp'])
        
        # Find sequences within time window
        patterns = defaultdict(list)
        
        for i in range(len(all_occurrences) - 1):
            current = all_occurrences[i]
            sequence = [current['incident_type']]
            timestamps = [current['timestamp']]
            
            # Look ahead for incidents within time window
            for j in range(i + 1, min(i + 10, len(all_occurrences))):
                next_inc = all_occurrences[j]
                time_diff = (next_inc['timestamp'] - current['timestamp']).total_seconds() / 60
                
                if time_diff <= time_window_minutes:
                    sequence.append(next_inc['incident_type'])
                    timestamps.append(next_inc['timestamp'])
                else:
                    break
            
            # Store sequences of length 2+
            if len(sequence) >= 2:
                pattern_key = " → ".join(sequence)
                patterns[pattern_key].append(timestamps)
        
        # Filter by support
        result = []
        for pattern, occurrences in patterns.items():
            if len(occurrences) >= min_support:
                # Calculate average cascade time
                cascade_times = []
                for timestamps in occurrences:
                    if len(timestamps) >= 2:
                        total_time = (timestamps[-1] - timestamps[0]).total_seconds()
                        cascade_times.append(total_time)
                
                avg_cascade_time = sum(cascade_times) / len(cascade_times) if cascade_times else 0
                
                result.append({
                    'pattern': pattern,
                    'occurrences': len(occurrences),
                    'confidence': len(occurrences) / len(incidents) if incidents else 0,
                    'avg_cascade_time_seconds': avg_cascade_time
                })
        
        # Sort by occurrences
        result.sort(key=lambda x: x['occurrences'], reverse=True)
        
        return result
    
    def check_active_pattern(self, recent_incidents, time_window_minutes=5):
        """
        Check if current incidents match a known pattern
        
        Args:
            recent_incidents: List of recent incident types with timestamps
            
        Returns:
            Matching pattern or None
        """
        known_patterns = self.mine_patterns(days=30, min_support=3)
        
        # Build current sequence
        if len(recent_incidents) < 2:
            return None
        
        current_sequence = " → ".join([inc['type'] for inc in recent_incidents])
        
        # Check if it matches any known pattern
        for pattern in known_patterns:
            if current_sequence in pattern['pattern'] or pattern['pattern'].startswith(current_sequence):
                return pattern
        
        return None