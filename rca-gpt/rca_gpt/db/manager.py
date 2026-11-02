"""
Database manager - handles all DB operations
"""
from sqlalchemy import create_engine, func, desc, and_
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import yaml
import re

from .models import Base, Incident, IncidentOccurrence, IncidentStats


class IncidentDatabase:
    """Manages incident storage and retrieval"""
    
    def __init__(self, config_path='config/config.yaml'):
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup database
        db_path = self.config['database']['path']
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(db_url, echo=False)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    @staticmethod
    def generate_fingerprint(incident_type, message):
        """
        Generate unique fingerprint for incident
        
        Args:
            incident_type: Type of incident
            message: Log message
            
        Returns:
            SHA256 hash string
        """
        # Normalize message: lowercase, remove numbers, extra spaces
        normalized = re.sub(r'\d+', '', message.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Create fingerprint
        fingerprint_string = f"{incident_type}:{normalized}"
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    def store_incident(self, incident_type, severity, message, 
                       timestamp=None, context_before=None, context_after=None):
        """
        Store an incident (creates new or updates existing)
        
        Args:
            incident_type: Type of incident
            severity: Log level (INFO/WARN/ERROR)
            message: Log message
            timestamp: When it occurred (default: now)
            context_before: List of logs before incident
            context_after: List of logs after incident
            
        Returns:
            Tuple of (incident, occurrence, is_new)
        """
        session = self.get_session()
        
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Generate fingerprint
            fingerprint = self.generate_fingerprint(incident_type, message)
            
            # Check if incident exists
            incident = session.query(Incident).filter_by(fingerprint=fingerprint).first()
            
            is_new = False
            if incident is None:
                # Create new incident
                incident = Incident(
                    fingerprint=fingerprint,
                    incident_type=incident_type,
                    severity=severity,
                    message_template=message,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    occurrence_count=1
                )
                session.add(incident)
                session.flush()  # Get ID
                is_new = True
            else:
                # Update existing incident
                incident.last_seen = timestamp
                incident.occurrence_count += 1
                incident.severity = max(incident.severity, severity, key=lambda x: ['INFO', 'WARN', 'ERROR'].index(x))
            
            # Create occurrence record
            occurrence = IncidentOccurrence(
                incident_id=incident.id,
                timestamp=timestamp,
                log_level=severity,
                full_message=message
            )
            
            # Store context
            if context_before:
                occurrence.set_context_before(context_before)
            if context_after:
                occurrence.set_context_after(context_after)
            
            session.add(occurrence)
            session.commit()
            
            return incident, occurrence, is_new
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_incident_by_id(self, incident_id):
        """Get incident by ID"""
        session = self.get_session()
        try:
            return session.query(Incident).filter_by(id=incident_id).first()
        finally:
            session.close()
    
    def get_incident_by_fingerprint(self, fingerprint):
        """Get incident by fingerprint"""
        session = self.get_session()
        try:
            return session.query(Incident).filter_by(fingerprint=fingerprint).first()
        finally:
            session.close()
    
    def get_recent_incidents(self, limit=50, incident_type=None):
        """
        Get most recent incidents
        
        Args:
            limit: Max number to return
            incident_type: Filter by type (optional)
            
        Returns:
            List of Incident objects
        """
        session = self.get_session()
        try:
            query = session.query(Incident).order_by(desc(Incident.last_seen))
            
            if incident_type:
                query = query.filter_by(incident_type=incident_type)
            
            return query.limit(limit).all()
        finally:
            session.close()
    
    def get_incident_occurrences(self, incident_id, limit=100):
        """Get all occurrences for an incident"""
        session = self.get_session()
        try:
            return session.query(IncidentOccurrence)\
                .filter_by(incident_id=incident_id)\
                .order_by(desc(IncidentOccurrence.timestamp))\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def get_incidents_in_timerange(self, start_time, end_time=None, incident_type=None):
        """
        Get incidents within time range
        
        Args:
            start_time: Start datetime
            end_time: End datetime (default: now)
            incident_type: Filter by type (optional)
            
        Returns:
            List of Incident objects
        """
        if end_time is None:
            end_time = datetime.utcnow()
        
        session = self.get_session()
        try:
            query = session.query(Incident).filter(
                and_(
                    Incident.last_seen >= start_time,
                    Incident.last_seen <= end_time
                )
            )
            
            if incident_type:
                query = query.filter_by(incident_type=incident_type)
            
            return query.order_by(desc(Incident.last_seen)).all()
        finally:
            session.close()
    
    def get_incident_stats(self, days=7):
        """
        Get incident statistics for last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with stats by incident type
        """
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Count by type
            stats = session.query(
                Incident.incident_type,
                func.count(Incident.id).label('unique_incidents'),
                func.sum(Incident.occurrence_count).label('total_occurrences')
            ).filter(
                Incident.last_seen >= cutoff
            ).group_by(
                Incident.incident_type
            ).all()
            
            result = {}
            for incident_type, unique, total in stats:
                result[incident_type] = {
                    'unique_incidents': unique,
                    'total_occurrences': total,
                    'avg_occurrences_per_incident': total / unique if unique > 0 else 0
                }
            
            return result
        finally:
            session.close()
    
    def mark_resolved(self, occurrence_id, resolution_notes, resolved_by="system"):
        """
        Mark an incident occurrence as resolved
        
        Args:
            occurrence_id: ID of occurrence
            resolution_notes: How it was fixed
            resolved_by: Who resolved it
            
        Returns:
            Updated occurrence
        """
        session = self.get_session()
        try:
            occurrence = session.query(IncidentOccurrence).filter_by(id=occurrence_id).first()
            
            if occurrence:
                occurrence.resolved = True
                occurrence.resolution_notes = resolution_notes
                occurrence.resolved_at = datetime.utcnow()
                occurrence.resolved_by = resolved_by
                session.commit()
            
            return occurrence
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def search_incidents(self, search_term):
        """
        Search incidents by message content
        
        Args:
            search_term: Text to search for
            
        Returns:
            List of matching incidents
        """
        session = self.get_session()
        try:
            return session.query(Incident)\
                .filter(Incident.message_template.like(f'%{search_term}%'))\
                .order_by(desc(Incident.last_seen))\
                .all()
        finally:
            session.close()
    
    def get_top_incidents(self, limit=10, days=7):
        """
        Get most frequent incidents
        
        Args:
            limit: Number to return
            days: Look back period
            
        Returns:
            List of incidents ordered by occurrence_count
        """
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            return session.query(Incident)\
                .filter(Incident.last_seen >= cutoff)\
                .order_by(desc(Incident.occurrence_count))\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def get_database_summary(self):
        """Get overall database statistics"""
        session = self.get_session()
        try:
            total_incidents = session.query(func.count(Incident.id)).scalar()
            total_occurrences = session.query(func.count(IncidentOccurrence.id)).scalar()
            resolved_count = session.query(func.count(IncidentOccurrence.id))\
                .filter_by(resolved=True).scalar()
            
            # Oldest and newest
            oldest = session.query(func.min(Incident.first_seen)).scalar()
            newest = session.query(func.max(Incident.last_seen)).scalar()
            
            return {
                'total_unique_incidents': total_incidents,
                'total_occurrences': total_occurrences,
                'resolved_occurrences': resolved_count,
                'unresolved_occurrences': total_occurrences - resolved_count,
                'oldest_incident': oldest.isoformat() if oldest else None,
                'newest_incident': newest.isoformat() if newest else None
            }
        finally:
            session.close()