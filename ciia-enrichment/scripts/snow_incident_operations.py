import requests
from requests.auth import HTTPBasicAuth
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SNOW_INSTANCE = os.getenv('SNOW_INSTANCE')
SNOW_USER = os.getenv('SNOW_USER')
SNOW_PASSWORD = os.getenv('SNOW_PASSWORD')
BASE_URL = f"https://{SNOW_INSTANCE}/api/now/table/incident"

class ServiceNowAPI:
    def __init__(self):
        self.auth = HTTPBasicAuth(SNOW_USER, SNOW_PASSWORD)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def get_all_incidents(self, limit=20):
        response = requests.get(
            BASE_URL,
            auth=self.auth,
            headers=self.headers,
            params={
                "sysparm_query": f"opened_by.user_name={SNOW_USER}^ORDERBYDESCsys_created_on",
                "sysparm_limit": limit
            }
        )

        if response.status_code == 200:
            return response.json()['result']
        return []
    
    def get_incident_by_number(self, inc_number):
        """Fetch specific incident by number (e.g., INC0010001)"""
        response = requests.get(
            BASE_URL,
            auth=self.auth,
            headers=self.headers,
            params={"sysparm_query": f"number={inc_number}"}
        )
        
        if response.status_code == 200:
            results = response.json()['result']
            return results[0] if results else None
        return None
    
    def update_incident_work_notes(self, sys_id, work_notes):
        """Add work notes to an incident"""
        payload = {"work_notes": work_notes}
        
        response = requests.patch(
            f"{BASE_URL}/{sys_id}",
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        return response.status_code == 200
    
    def search_similar_incidents(self, keywords, limit=5):
        """Search for incidents with similar keywords"""
        query = "^".join([f"short_descriptionLIKE{kw}^ORdescriptionLIKE{kw}" for kw in keywords.split()])
        
        response = requests.get(
            BASE_URL,
            auth=self.auth,
            headers=self.headers,
            params={
                "sysparm_query": query,
                "sysparm_limit": limit
            }
        )
        
        if response.status_code == 200:
            return response.json()['result']
        return []
    
    def create_incident(self, short_desc, description, priority=3, category="Software"):
        """Create a new test incident"""
        payload = {
            "short_description": short_desc,
            "description": description,
            "priority": priority,
            "category": category,
            "assignment_group": ""
        }
        
        response = requests.post(
            BASE_URL,
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        if response.status_code == 201:
            return response.json()['result']
        else:
            print(f"Failed to create: {response.text}")
            return None


# Test functions
if __name__ == "__main__":
    snow = ServiceNowAPI()
    
    print("=== Fetching All Incidents ===")
    incidents = snow.get_all_incidents(limit=10)
    for inc in incidents:
        print(f"{inc['number']}: {inc['short_description']} (Priority: {inc['priority']})")
    
    print("\n=== Searching Similar Incidents ===")
    similar = snow.search_similar_incidents("database connection")
    for inc in similar:
        print(f"{inc['number']}: {inc['short_description']}")
    
    print("\n=== Testing Work Notes Update ===")
    if incidents:
        test_inc = incidents[0]
        success = snow.update_incident_work_notes(
            test_inc['sys_id'],
            f"[AUTO-ENRICHMENT TEST] Added by Python script at {datetime.now()}"
        )
        print(f"Work notes update: {'✅ Success' if success else '❌ Failed'}")