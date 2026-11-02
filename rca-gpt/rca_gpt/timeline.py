"""
Timeline analysis - what happened before the incident
"""
from datetime import timedelta
from .db.manager import IncidentDatabase


class TimelineAnalyzer:
    """Analyze incident timelines"""
    
    def __init__(self, config_path='config/config.yaml'):
        self.db = IncidentDatabase(config_path)
    
    def get_timeline(self, incident_id, minutes_before=10, minutes_after=5):
        """
        Get timeline of events around an incident
        
        Returns:
            Dict with timeline events
        """
        # Get incident
        incident = self.db.get_incident_by_id(incident_id)
        if not incident:
            return None
        
        # Get all occurrences
        occurrences = self.db.get_incident_occurrences(incident_id)
        if not occurrences:
            return None
        
        # Use first occurrence for timeline
        target_occ = occurrences[0]
        target_time = target_occ.timestamp
        
        # Get all incidents in time window
        start_time = target_time - timedelta(minutes=minutes_before)
        end_time = target_time + timedelta(minutes=minutes_after)
        
        related_incidents = self.db.get_incidents_in_timerange(start_time, end_time)
        
        # Build timeline
        events = []
        for inc in related_incidents:
            occs = self.db.get_incident_occurrences(inc.id, limit=100)
            for occ in occs:
                if start_time <= occ.timestamp <= end_time:
                    time_diff = (occ.timestamp - target_time).total_seconds() / 60
                    
                    events.append({
                        'timestamp': occ.timestamp,
                        'incident_type': inc.incident_type,
                        'message': occ.full_message,
                        'severity': occ.log_level,
                        'minutes_from_target': time_diff,
                        'is_target': occ.id == target_occ.id
                    })
        
        # Sort by time
        events.sort(key=lambda x: x['timestamp'])
        
        # Find "original sin" - first error before target
        original_sin = None
        for event in events:
            if event['minutes_from_target'] < 0 and event['severity'] == 'ERROR':
                original_sin = event
                break
        
        return {
            'target_incident': incident.to_dict(),
            'target_time': target_time,
            'events': events,
            'original_sin': original_sin,
            'total_events': len(events)
        }