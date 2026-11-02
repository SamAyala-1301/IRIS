from snow_incident_operations import ServiceNowAPI
import time

snow = ServiceNowAPI()

# Create 3 test incidents
test_incidents = [
    {
        "short_desc": "Website certificate expired",
        "description": "Users seeing SSL warning on main website. Certificate shows expired yesterday.",
        "priority": 1
    },
    {
        "short_desc": "Backup job failed overnight",
        "description": "Nightly backup to tape failed with error code 0x8007045D. Disk space OK.",
        "priority": 3
    },
    {
        "short_desc": "User account locked after password reset",
        "description": "User reports account locked immediately after mandatory password change. Cannot login.",
        "priority": 2
    }
]

for test in test_incidents:
    print(f"Creating: {test['short_desc']}")
    inc = snow.create_incident(
        test['short_desc'],
        test['description'],
        test['priority']
    )
    
    if inc:
        print(f"✅ Created {inc['number']}")
        # Simulate assignment (you'd do this in ServiceNow UI)
        # snow.update_incident_assignment_group(inc['sys_id'], 'L3 Support')
    
    time.sleep(2)

print("\n✅ Test incidents created! Now assign them to L3 in ServiceNow to trigger enrichment.")