"""
Database models for incident storage
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, 
    DateTime, Boolean, ForeignKey, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class Incident(Base):
    """Unique incidents (deduplicated by fingerprint)"""
    __tablename__ = 'incidents'
    
    id = Column(Integer, primary_key=True)
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    incident_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(10), nullable=False)  # INFO, WARN, ERROR
    message_template = Column(Text, nullable=False)
    
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    occurrence_count = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    occurrences = relationship("IncidentOccurrence", back_populates="incident")
    
    def __repr__(self):
        return f"<Incident(id={self.id}, type={self.incident_type}, count={self.occurrence_count})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'fingerprint': self.fingerprint,
            'incident_type': self.incident_type,
            'severity': self.severity,
            'message_template': self.message_template,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'occurrence_count': self.occurrence_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class IncidentOccurrence(Base):
    """Individual incident occurrences with context"""
    __tablename__ = 'incident_occurrences'
    
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey('incidents.id'), nullable=False, index=True)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    log_level = Column(String(10), nullable=False)
    full_message = Column(Text, nullable=False)
    
    # Context: JSON strings containing surrounding logs
    context_before = Column(Text)  # JSON array of 5 logs before
    context_after = Column(Text)   # JSON array of 5 logs after
    
    # Resolution tracking
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="occurrences")
    
    def __repr__(self):
        return f"<IncidentOccurrence(id={self.id}, incident_id={self.incident_id}, timestamp={self.timestamp})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'log_level': self.log_level,
            'full_message': self.full_message,
            'context_before': json.loads(self.context_before) if self.context_before else [],
            'context_after': json.loads(self.context_after) if self.context_after else [],
            'resolved': self.resolved,
            'resolution_notes': self.resolution_notes,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def set_context_before(self, logs):
        """Set context_before from list of log dicts"""
        self.context_before = json.dumps(logs)
    
    def set_context_after(self, logs):
        """Set context_after from list of log dicts"""
        self.context_after = json.dumps(logs)
    
    def get_context_before(self):
        """Get context_before as list"""
        return json.loads(self.context_before) if self.context_before else []
    
    def get_context_after(self):
        """Get context_after as list"""
        return json.loads(self.context_after) if self.context_after else []


class IncidentStats(Base):
    """Daily aggregated statistics"""
    __tablename__ = 'incident_stats'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    incident_type = Column(String(50), nullable=False)
    
    total_count = Column(Integer, default=0)
    unique_count = Column(Integer, default=0)
    avg_resolution_time = Column(Float)  # seconds
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<IncidentStats(date={self.date}, type={self.incident_type}, count={self.total_count})>"
    
    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'incident_type': self.incident_type,
            'total_count': self.total_count,
            'unique_count': self.unique_count,
            'avg_resolution_time': self.avg_resolution_time
        }