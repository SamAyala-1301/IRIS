"""
CIIA Enhanced Vercel Function with Intelligent Context Retrieval
Fixed version - handles ServiceNow API response correctly
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

try:
    from groq import Groq
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError as e:
    print(f"Import error: {e}")


class handler(BaseHTTPRequestHandler):
    """Enhanced Vercel serverless handler with smart context"""
    
    def do_POST(self):
        """Handle POST requests from ServiceNow"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            if 'incident_sys_id' not in body:
                self.send_error_response(400, 'Missing incident_sys_id')
                return
            
            snow_instance = os.environ.get('SNOW_INSTANCE')
            snow_user = os.environ.get('SNOW_USER')
            snow_password = os.environ.get('SNOW_PASSWORD')
            groq_api_key = os.environ.get('GROQ_API_KEY')
            
            if not all([snow_instance, snow_user, snow_password, groq_api_key]):
                self.send_error_response(500, 'Missing environment variables')
                return
            
            incident_sys_id = body['incident_sys_id']
            
            result = self.enrich_incident(
                incident_sys_id,
                snow_instance,
                snow_user,
                snow_password,
                groq_api_key
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.send_error_response(500, f"{str(e)} | Trace: {error_detail}")
    
    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            'status': 'healthy',
            'service': 'CIIA Enhanced Enrichment API',
            'version': '2.0.1'
        }
        self.wfile.write(json.dumps(response).encode())
    
    def send_error_response(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error = {'error': message}
        self.wfile.write(json.dumps(error).encode())
    
    def enrich_incident(self, incident_sys_id, snow_instance, snow_user, snow_password, groq_api_key):
        """Main enrichment logic with intelligent context"""
        
        # 1. Fetch current incident with ALL fields
        incident = self.fetch_incident_detailed(
            incident_sys_id,
            snow_instance,
            snow_user,
            snow_password
        )
        
        # 2. Intelligent similar incident search
        similar_incidents = self.search_similar_incidents_smart(
            incident,
            snow_instance,
            snow_user,
            snow_password
        )
        
        # 3. Extract resolutions from similar tickets
        resolution_knowledge = self.extract_resolution_intelligence(
            similar_incidents
        )
        
        # 4. Two-stage AI analysis
        analysis = self.analyze_with_groq_enhanced(
            incident,
            similar_incidents,
            resolution_knowledge,
            groq_api_key
        )
        
        # 5. Format enrichment
        enrichment = self.format_enrichment_enhanced(
            analysis,
            similar_incidents,
            resolution_knowledge
        )
        
        # 6. Update incident
        incident_url = f"https://{snow_instance}/api/now/table/incident/{incident_sys_id}"
        auth = HTTPBasicAuth(snow_user, snow_password)
        
        update_response = requests.patch(
            incident_url,
            auth=auth,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"work_notes": enrichment})
        )
        
        if update_response.status_code != 200:
            raise Exception(f'Failed to update incident: {update_response.text}')
        
        return {
            'status': 'success',
            'incident_number': incident.get('number', 'Unknown'),
            'similar_found': len(similar_incidents),
            'resolutions_extracted': len(resolution_knowledge),
            'enriched_at': datetime.utcnow().isoformat()
        }
    
    def fetch_incident_detailed(self, incident_sys_id, snow_instance, snow_user, snow_password):
        """Fetch incident with all relevant fields - FIXED VERSION"""
        
        incident_url = f"https://{snow_instance}/api/now/table/incident/{incident_sys_id}"
        auth = HTTPBasicAuth(snow_user, snow_password)
        
        response = requests.get(
            incident_url,
            auth=auth,
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f'Failed to fetch incident: HTTP {response.status_code} - {response.text}')
        
        data = response.json()
        
        # FIX: Handle both possible response structures
        if 'result' in data:
            incident = data['result']
        else:
            incident = data
        
        # Ensure sys_id is in the incident data
        if 'sys_id' not in incident:
            incident['sys_id'] = incident_sys_id
        
        return incident
    
    def search_similar_incidents_smart(self, incident, snow_instance, snow_user, snow_password):
        """Multi-strategy search for truly similar incidents"""
        
        auth = HTTPBasicAuth(snow_user, snow_password)
        base_url = f"https://{snow_instance}/api/now/table/incident"
        
        all_similar = []
        seen_sys_ids = {incident.get('sys_id', '')}
        
        # Get incident sys_id safely
        current_sys_id = incident.get('sys_id', '')
        
        # Strategy 1: Exact category match with resolved tickets
        category = incident.get('category', '')
        if category:
            query1 = f"category={category}^state=6^ORstate=7^sys_id!={current_sys_id}"
            results1 = self._execute_search(base_url, auth, query1, limit=10)
            all_similar.extend(results1)
            seen_sys_ids.update(r.get('sys_id', '') for r in results1)
        
        # Strategy 2: Keywords from description
        keywords = self._extract_technical_keywords(incident)
        if keywords:
            keyword_queries = []
            for kw in keywords[:3]:
                keyword_queries.append(f"short_descriptionLIKE{kw}")
            
            if keyword_queries:
                query2 = '^OR'.join(keyword_queries) + f"^state=6^ORstate=7^sys_id!={current_sys_id}"
                results2 = self._execute_search(base_url, auth, query2, limit=15)
                
                # Filter out already seen
                results2 = [r for r in results2 if r.get('sys_id', '') not in seen_sys_ids]
                all_similar.extend(results2)
                seen_sys_ids.update(r.get('sys_id', '') for r in results2)
        
        # Strategy 3: Same CI (Configuration Item)
        cmdb_ci = incident.get('cmdb_ci', '')
        if cmdb_ci:
            query3 = f"cmdb_ci={cmdb_ci}^state=6^ORstate=7^sys_id!={current_sys_id}"
            results3 = self._execute_search(base_url, auth, query3, limit=10)
            results3 = [r for r in results3 if r.get('sys_id', '') not in seen_sys_ids]
            all_similar.extend(results3)
        
        # Rank by relevance if too many
        if len(all_similar) > 10:
            all_similar = self._rank_by_relevance(incident, all_similar)[:10]
        
        return all_similar[:5]  # Return top 5
    
    def _execute_search(self, url, auth, query, limit=10):
        """Execute ServiceNow query"""
        try:
            response = requests.get(
                url,
                auth=auth,
                headers={"Accept": "application/json"},
                params={
                    'sysparm_query': query,
                    'sysparm_limit': limit
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result', [])
        except Exception as e:
            print(f"Search error: {e}")
        
        return []
    
    def _extract_technical_keywords(self, incident):
        """Extract technical keywords (error codes, system names, etc.)"""
        
        short_desc = incident.get('short_description', '')
        description = incident.get('description', '')
        text = (short_desc + ' ' + description).upper()
        
        keywords = []
        
        # Extract error codes (ERW, E001, HTTP 500, etc.)
        error_patterns = [
            r'\b[A-Z]{2,4}\d{2,4}\b',
            r'\bERROR\s*[:\-]?\s*\d+\b',
            r'\b[A-Z]+\s*\d{3,4}\b',
            r'\b\d{3}\s*ERROR\b',
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        # Extract application names (all caps words)
        app_names = re.findall(r'\b[A-Z]{3,}(?:\s+[A-Z]{3,})*\b', text)
        keywords.extend(app_names)
        
        # Extract technical terms
        technical_terms = ['TIMEOUT', 'CONNECTION', 'DATABASE', 'LOGIN', 'AUTH',
                          'PERMISSION', 'DENIED', 'FAILED', 'ERROR', 'EXCEPTION',
                          'CRASH', 'FREEZE', 'SLOW', 'LATENCY', 'UNAVAILABLE']
        
        for term in technical_terms:
            if term in text:
                keywords.append(term)
        
        # Deduplicate and return top 5
        keywords = list(set(keywords))
        return keywords[:5]
    
    def _rank_by_relevance(self, current_incident, similar_incidents):
        """Simple relevance ranking"""
        
        current_desc = (current_incident.get('short_description', '') + ' ' +
                       current_incident.get('description', '')).lower()
        current_words = set(current_desc.split())
        
        scored = []
        for inc in similar_incidents:
            inc_desc = (inc.get('short_description', '') + ' ' +
                       inc.get('description', '')).lower()
            inc_words = set(inc_desc.split())
            
            # Jaccard similarity
            intersection = len(current_words & inc_words)
            union = len(current_words | inc_words)
            score = intersection / union if union > 0 else 0
            
            # Boost if same category
            if inc.get('category') == current_incident.get('category'):
                score += 0.2
            
            # Boost if has resolution notes
            if inc.get('close_notes') or inc.get('work_notes'):
                score += 0.1
            
            scored.append((score, inc))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [inc for score, inc in scored]
    
    def extract_resolution_intelligence(self, similar_incidents):
        """Extract actual resolutions and workarounds from similar tickets"""
        
        resolutions = []
        
        for inc in similar_incidents:
            resolution_data = {
                'incident_number': inc.get('number', 'Unknown'),
                'short_description': inc.get('short_description', '')[:100],
                'resolution': None,
                'workaround': None,
                'root_cause': None
            }
            
            # Combine all resolution sources
            all_notes = []
            if inc.get('close_notes'):
                all_notes.append(('close_notes', inc['close_notes']))
            if inc.get('work_notes'):
                all_notes.append(('work_notes', inc['work_notes']))
            
            for source, notes in all_notes:
                if not notes:
                    continue
                    
                notes_lower = notes.lower()
                
                # Extract resolution
                resolution_keywords = ['resolution:', 'resolved by', 'fix:', 'fixed by', 'solution:']
                for keyword in resolution_keywords:
                    if keyword in notes_lower:
                        idx = notes_lower.index(keyword)
                        resolution_text = notes[idx:idx+200].strip()
                        if resolution_text:
                            resolution_data['resolution'] = resolution_text
                            break
                
                # Extract workaround
                workaround_keywords = ['workaround:', 'temporary fix', 'interim solution']
                for keyword in workaround_keywords:
                    if keyword in notes_lower:
                        idx = notes_lower.index(keyword)
                        workaround_text = notes[idx:idx+200].strip()
                        if workaround_text:
                            resolution_data['workaround'] = workaround_text
                            break
                
                # Extract root cause
                rootcause_keywords = ['root cause:', 'caused by', 'issue was']
                for keyword in rootcause_keywords:
                    if keyword in notes_lower:
                        idx = notes_lower.index(keyword)
                        rootcause_text = notes[idx:idx+200].strip()
                        if rootcause_text:
                            resolution_data['root_cause'] = rootcause_text
                            break
            
            # If no structured resolution found, extract last work note
            if not resolution_data['resolution'] and inc.get('work_notes'):
                resolution_data['resolution'] = inc['work_notes'][-300:].strip()
            
            if resolution_data['resolution'] or resolution_data['workaround']:
                resolutions.append(resolution_data)
        
        return resolutions[:5]
    
    def analyze_with_groq_enhanced(self, incident, similar_incidents, resolutions, api_key):
        """Enhanced AI analysis with resolution context"""
        
        groq_client = Groq(api_key=api_key)
        
        # Build context
        context = self._build_analysis_context(incident, similar_incidents, resolutions)
        
        prompt = f"""You are an expert L3 IT incident analyst. Analyze this incident using historical resolution data.

**CURRENT INCIDENT:**
Number: {incident.get('number', 'N/A')}
Description: {incident.get('short_description', 'N/A')}
Details: {incident.get('description', 'No details')}
Category: {incident.get('category', 'Unknown')} / {incident.get('subcategory', 'N/A')}
Priority: {incident.get('priority', 'Unknown')} (1=Critical, 5=Low)

**HISTORICAL RESOLUTION DATA:**
{context['resolutions_text']}

**SIMILAR INCIDENTS:**
{context['similar_summary']}

**YOUR ANALYSIS:**

1. **Severity Validation**
   - Is the current priority appropriate?

2. **Root Cause Hypotheses**
   - Top 2-3 probable causes
   - Reference similar incidents

3. **Proven Workarounds**
   - Solutions that worked in similar cases
   - Include incident numbers

4. **Recommended Actions**
   - Step-by-step troubleshooting
   - Based on historical resolutions

5. **Estimated Resolution Time**

Be specific. Reference incident numbers. Cite proven solutions."""

        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a senior L3 incident analyst."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.5,
                max_tokens=2000
            )
            
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"AI Analysis unavailable: {str(e)}\n\nPlease review similar incidents manually."
    
    def _build_analysis_context(self, incident, similar_incidents, resolutions):
        """Build structured context for AI"""
        
        if resolutions:
            resolutions_text = f"Found {len(resolutions)} resolved similar incidents:\n\n"
            for idx, res in enumerate(resolutions, 1):
                resolutions_text += f"{idx}. {res['incident_number']}: {res['short_description']}\n"
                if res['root_cause']:
                    resolutions_text += f"   Root Cause: {res['root_cause']}\n"
                if res['resolution']:
                    resolutions_text += f"   Resolution: {res['resolution']}\n"
                resolutions_text += "\n"
        else:
            resolutions_text = "No detailed resolutions found."
        
        if similar_incidents:
            similar_summary = f"Found {len(similar_incidents)} similar incidents:\n"
            for inc in similar_incidents[:5]:
                similar_summary += f"- {inc.get('number', 'N/A')}: {inc.get('short_description', 'N/A')[:80]}\n"
        else:
            similar_summary = "No similar incidents found."
        
        return {
            'resolutions_text': resolutions_text,
            'similar_summary': similar_summary
        }
    
    def format_enrichment_enhanced(self, analysis, similar_incidents, resolutions):
        """Format enhanced enrichment"""
        
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        enrichment = f"""
╔══════════════════════════════════════════════════════════════╗
║     🤖 AI-POWERED INCIDENT ENRICHMENT v2.0                  ║
║     Generated: {timestamp}                   ║
╚══════════════════════════════════════════════════════════════╝

{analysis}

{'='*65}
📊 INTELLIGENCE SOURCES:
- Similar incidents: {len(similar_incidents)}
- Resolutions extracted: {len(resolutions)}
- Confidence: {'High' if len(resolutions) >= 2 else 'Moderate'}
{'='*65}

💡 SIMILAR INCIDENTS:
"""
        
        if similar_incidents:
            for inc in similar_incidents[:5]:
                enrichment += f"   • {inc.get('number', 'N/A')}: {inc.get('short_description', 'N/A')[:70]}...\n"
        else:
            enrichment += "   • None found\n"
        
        enrichment += f"""
{'='*65}
🔧 CIIA v2.0 - Contextual Incident Intelligence Agent
⚡ Powered by Groq AI + Resolution Intelligence
"""
        
        return enrichment