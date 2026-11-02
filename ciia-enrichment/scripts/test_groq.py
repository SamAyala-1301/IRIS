from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def test_basic_call():
    """Test basic Groq API call"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say 'Hello from Groq!' if you can hear me.",
            }
        ],
        model="llama-3.1-8b-instant",  # Free model
    )
    
    print("✅ Groq Response:")
    print(chat_completion.choices[0].message.content)

def analyze_incident(incident_description):
    """Test incident analysis"""
    prompt = f"""You are an IT incident analyzer. Analyze this incident and provide:
    1. Severity Assessment (critical/high/medium/low)
    2. Top 3 Probable Root Causes
    3. Suggested Next Steps

    Incident: {incident_description}
    
    Be concise and technical."""
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert IT operations analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=1024
    )
    
    return chat_completion.choices[0].message.content

if __name__ == "__main__":
    print("=== Testing Basic Connection ===")
    test_basic_call()
    
    print("\n=== Testing Incident Analysis ===")
    test_incident = "Database connection pool exhausted. Production DB throwing 'max connections reached' error. Started after deployment."
    analysis = analyze_incident(test_incident)
    print(analysis)
