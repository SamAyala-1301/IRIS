from groq import Groq
import os
import json
from dotenv import load_dotenv
from snow_incident_operations import ServiceNowAPI
from datetime import datetime

load_dotenv()

class IncidentEnrichmentEngine:
    def __init__(self):
        self.snow = ServiceNowAPI()
        self.groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    def extract_keywords(self, text):
        """Extract key technical terms from incident description"""
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 4]
        return ' '.join(keywords[:5])
    
    def get_historical_context(self, incident):
        """Fetch similar past incidents"""
        keywords = self.extract_keywords(incident['short_description'] + ' ' + incident.get('description', ''))
        similar = self.snow.search_similar_incidents(keywords, limit=3)
        
        context = []
        for inc in similar:
            if inc['sys_id'] != incident['sys_id']:
                context.append({
                    'number': inc['number'],
                    'description': inc['short_description'],
                    'state': inc['state'],
                    'resolution': inc.get('close_notes', 'Not resolved yet')
                })
        
        return context
    
    def analyze_with_groq(self, incident, historical_context):
        """Send incident to Groq for analysis"""
        
        historical_text = "\n".join([
            f"- {inc['number']}: {inc['description']} (Resolution: {inc['resolution']})"
            for inc in historical_context
        ]) if historical_context else "No similar incidents found."
        
        prompt = f"""You are an expert IT incident analyst. Analyze this ServiceNow incident and provide actionable intelligence.

**Current Incident:**
- Number: {incident['number']}
- Short Description: {incident['short_description']}
- Full Description: {incident.get('description', 'No details provided')}
- Category: {incident.get('category', 'Unknown')}
- Priority: {incident.get('priority', 'Unknown')}

**Similar Past Incidents:**
{historical_text}

**Provide:**
1. **Severity Validation**: Is the current priority appropriate? Why/why not?
2. **Root Cause Hypotheses**: Top 3 most likely causes based on description and historical patterns
3. **Missing Information**: What critical details are missing that L1/L2 should have gathered?
4. **Recommended Actions**: Specific troubleshooting steps in order of likelihood
5. **Estimated Resolution Time**: Based on similar incidents

Format as clear, structured text with headers. Be specific and technical."""

        chat_completion = self.groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert IT operations analyst with 15 years of experience in incident management."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=2048
        )
        
        return chat_completion.choices[0].message.content
    
    def enrich_incident(self, incident_number):
        """Main enrichment workflow"""
        print(f"\n🔍 Enriching incident: {incident_number}")
        
        # Step 1: Fetch incident
        incident = self.snow.get_incident_by_number(incident_number)
        if not incident:
            print(f"❌ Incident {incident_number} not found")
            return False
        
        print(f"✅ Incident found: {incident['short_description']}")
        
        # Step 2: Get historical context
        print("📚 Searching for similar past incidents...")
        historical = self.get_historical_context(incident)
        print(f"✅ Found {len(historical)} similar incidents")
        
        # Step 3: Analyze with Groq
        print("🤖 Analyzing with Groq AI (Llama 3.1)...")
        analysis = self.analyze_with_groq(incident, historical)
        print("✅ Analysis complete")
        
        # Step 4: Format enrichment
        enrichment = f"""
╔══════════════════════════════════════════════════════════════╗
║          🤖 AI-POWERED INCIDENT ENRICHMENT                  ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                        ║
║          Model: Llama 3.1 via Groq                          ║
╚══════════════════════════════════════════════════════════════╝

{analysis}

═══════════════════════════════════════════════════════════════
📊 HISTORICAL CONTEXT:
{len(historical)} similar incident(s) found in ServiceNow
═══════════════════════════════════════════════════════════════

---
🔧 This enrichment was automatically generated by CIIA
(Contextual Incident Intelligence Agent)
Powered by Groq AI - 100% Free Tier
"""
        
        # Step 5: Update work notes
        print("💾 Updating incident work notes...")
        success = self.snow.update_incident_work_notes(incident['sys_id'], enrichment)
        
        if success:
            print(f"✅ SUCCESS! Incident {incident_number} has been enriched")
            print("\n" + "="*60)
            print(enrichment)
            print("="*60)
            return True
        else:
            print("❌ Failed to update work notes")
            return False


if __name__ == "__main__":
    engine = IncidentEnrichmentEngine()
    
    # Test with your first incident
    engine.enrich_incident("INC0010001")