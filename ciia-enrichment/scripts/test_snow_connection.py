import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()

SNOW_INSTANCE = os.getenv("SNOW_INSTANCE")
SNOW_USER = os.getenv("SNOW_USER")
SNOW_PASSWORD = os.getenv("SNOW_PASSWORD")

BASE_URL = f"https://{SNOW_INSTANCE}/api/now/table/incident"

def test_connection():
    try:
        response = requests.get(
            BASE_URL,
            auth=HTTPBasicAuth(SNOW_USER, SNOW_PASSWORD),
            headers={"Accept": "application/json"},
            params={"sysparm_limit": 1}
        )

        print("Status Code:", response.status_code)

        if response.status_code == 200:
            print("✅ SUCCESS! Connected to ServiceNow")
            print(response.json())
            return True
        else:
            print("❌ FAILED")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_connection()
