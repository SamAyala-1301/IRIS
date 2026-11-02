#!/usr/bin/env python3
"""
Generate test incidents for demonstration
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rca_gpt.db.manager import IncidentDatabase


def generate_test_incidents(count=50):
    """Generate realistic test incidents"""
    db = IncidentDatabase()
    
    incident_templates = [
        ('Auth Error', 'ERROR', 'Invalid token'),
        ('Auth Error', 'ERROR', 'Authentication failed'),
        ('Auth Error', 'WARN', 'Token expired'),
        ('Timeout', 'ERROR', 'Request timeout'),
        ('Timeout', 'WARN', 'Connection timeout'),
        ('DB Error', 'ERROR', 'Connection refused'),
        ('DB Error', 'ERROR', 'Query timeout'),
        ('DB Error', 'WARN', 'Slow query detected'),
        ('Normal', 'INFO', 'Login success'),
        ('Normal', 'INFO', 'Request completed'),
    ]
    
    print(f"🎲 Generating {count} test incidents...")
    
    # Generate incidents over last 7 days
    now = datetime.utcnow()
    
    for i in range(count):
        # Random timestamp in last 7 days
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Random incident
        incident_type, severity, message = random.choice(incident_templates)
        
        # Add some variation to messages
        variations = ['', ' - retry failed', ' - host unreachable', ' - service unavailable']
        message = message + random.choice(variations)
        
        # Store
        incident, occurrence, is_new = db.store_incident(
            incident_type=incident_type,
            severity=severity,
            message=message,
            timestamp=timestamp,
            context_before=[
                {'level': 'INFO', 'timestamp': timestamp.isoformat(), 'message': 'Previous log 1'},
                {'level': 'INFO', 'timestamp': timestamp.isoformat(), 'message': 'Previous log 2'}
            ],
            context_after=[
                {'level': 'WARN', 'timestamp': timestamp.isoformat(), 'message': 'Following log 1'}
            ]
        )
        
        status = "NEW" if is_new else "DUP"
        print(f"  [{i+1}/{count}] {status} - {incident_type}: {message[:40]}")
    
    print(f"\n✅ Generated {count} test incidents")
    
    # Show summary
    summary = db.get_database_summary()
    print(f"\n📊 Database now contains:")
    print(f"   Unique incidents: {summary['total_unique_incidents']}")
    print(f"   Total occurrences: {summary['total_occurrences']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate test incidents')
    parser.add_argument('--count', type=int, default=50, help='Number of incidents to generate')
    args = parser.parse_args()
    
    generate_test_incidents(args.count)