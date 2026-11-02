import requests
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from snow_incident_operations import ServiceNowAPI

load_dotenv()

# Your Vercel URL
VERCEL_URL = "https://ciia-enrichment.vercel.app/api/enrich"

def test_health_check():
    """Test GET endpoint (health check)"""
    print("=" * 60)
    print("1. HEALTH CHECK TEST (GET)")
    print("=" * 60)
    
    try:
        response = requests.get(VERCEL_URL)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("✅ Health check PASSED")
            return True
        else:
            print("❌ Health check FAILED")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_enrichment(incident_sys_id):
    """Test POST endpoint (actual enrichment)"""
    print("\n" + "=" * 60)
    print("2. ENRICHMENT TEST (POST)")
    print("=" * 60)
    
    payload = {
        "incident_sys_id": incident_sys_id
    }
    
    print(f"Testing with incident sys_id: {incident_sys_id}")
    print(f"Sending POST to: {VERCEL_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(
            VERCEL_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # 30 second timeout
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✅ Enrichment PASSED")
            print("👉 Check ServiceNow work notes for the AI enrichment!")
            return True
        else:
            print("\n❌ Enrichment FAILED")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (function took >30s)")
        print("This might mean the function is still processing. Check ServiceNow in a minute.")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def get_first_incident_sys_id():
    """Get first incident from ServiceNow automatically"""
    try:
        print("\n📡 Fetching incidents from ServiceNow...")
        snow = ServiceNowAPI()
        incidents = snow.get_all_incidents(limit=5)
        
        if not incidents:
            print("❌ No incidents found in ServiceNow")
            return None
        
        print(f"✅ Found {len(incidents)} incidents\n")
        print("Available incidents:")
        for idx, inc in enumerate(incidents, 1):
            print(f"  {idx}. {inc['number']} - {inc['short_description'][:50]}...")
        
        # Use first incident
        first_inc = incidents[0]
        print(f"\n✅ Using incident: {first_inc['number']} (sys_id: {first_inc['sys_id']})")
        return first_inc['sys_id']
        
    except Exception as e:
        print(f"❌ ERROR fetching incidents: {e}")
        return None

if __name__ == "__main__":
    print("\n🚀 CIIA VERCEL ENDPOINT TEST\n")
    
    # Test 1: Health check
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n❌ Health check failed. Fix this before testing enrichment.")
        sys.exit(1)
    
    # Test 2: Enrichment
    print("\n" + "=" * 60)
    print("ENRICHMENT TEST OPTIONS")
    print("=" * 60)
    print("1. Auto-fetch first incident from ServiceNow")
    print("2. Enter incident sys_id manually")
    print("3. Skip enrichment test")
    
    try:
        choice = input("\nChoose option (1/2/3): ").strip()
        
        if choice == "1":
            test_sys_id = get_first_incident_sys_id()
            if test_sys_id:
                test_enrichment(test_sys_id)
            else:
                print("❌ Could not fetch incident automatically")
        
        elif choice == "2":
            test_sys_id = input("Enter incident sys_id: ").strip()
            if test_sys_id:
                test_enrichment(test_sys_id)
            else:
                print("❌ No sys_id provided")
        
        else:
            print("⏭️  Skipping enrichment test")
    
    except KeyboardInterrupt:
        print("\n\n⏭️  Test interrupted by user")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)