import requests
import json

CLOUD_FUNCTION_URL = "YOUR_CLOUD_FUNCTION_URL_HERE"

def test_enrichment(incident_sys_id):
    payload = {
        "incident_sys_id": incident_sys_id
    }
    
    response = requests.post(
        CLOUD_FUNCTION_URL,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    # Get sys_id from ServiceNow (open incident, check URL)
    test_incident_sys_id = "YOUR_INCIDENT_SYS_ID"
    test_enrichment(test_incident_sys_id)
