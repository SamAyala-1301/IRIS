#!/usr/bin/env python3
"""Generate realistic cascading incident patterns"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from rca_gpt.db.manager import IncidentDatabase

def generate_cascades(count=20):
    """Generate cascading incident patterns"""
    db = IncidentDatabase()
    
    # Define cascade patterns
    cascades = [
        ['Auth Error', 'Timeout', 'DB Error'],
        ['DB Error', 'Timeout'],
        ['Timeout', 'Auth Error'],
        ['Auth Error', 'Auth Error', 'DB Error'],
    ]
    
    print(f"🔗 Generating {count} cascade patterns...")
    
    now = datetime.utcnow()
    
    for i in range(count):
        # Pick random cascade
        cascade = random.choice(cascades)
        
        # Random start time in last 30 days
        days_ago = random.randint(0, 30)
        base_time = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # Create cascade with 1-3 minute gaps
        for j, incident_type in enumerate(cascade):
            timestamp = base_time + timedelta(minutes=j * random.randint(1, 3))
            
            messages = {
                'Auth Error': ['Invalid token', 'Authentication failed', 'Token expired'],
                'Timeout': ['Request timeout', 'Connection timeout', 'Service timeout'],
                'DB Error': ['Connection refused', 'Query timeout', 'Database unavailable']
            }
            
            message = random.choice(messages[incident_type])
            
            db.store_incident(
                incident_type=incident_type,
                severity='ERROR',
                message=message,
                timestamp=timestamp
            )
        
        print(f"  Cascade {i+1}: {' → '.join(cascade)}")
    
    print(f"\n✅ Generated {count} cascading patterns")
    print("\nNow run: python -m rca_gpt.cli patterns --days 30")

if __name__ == "__main__":
    generate_cascades(30)