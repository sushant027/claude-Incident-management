"""
AI service using Google Gemini
"""
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from config import settings

# Import Gemini only if available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class AIService:
    """AI service for similar incident detection and report generation"""
    
    def __init__(self):
        self.enabled = settings.ai_enabled and GEMINI_AVAILABLE
        if self.enabled:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    def find_similar_incidents(
        self,
        title: str,
        description: str,
        exception_text: Optional[str],
        service_name: str,
        historical_incidents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use AI to find similar incidents and provide recommendations
        """
        if not self.enabled:
            return {
                "similar_incidents": [],
                "similarity_reasons": {},
                "recommendation_text": "AI service not available. Please configure GEMINI_API_KEY."
            }
        
        try:
            # Prepare historical incidents context
            incidents_context = "\n\n".join([
                f"Incident #{inc['id']}:\n"
                f"Title: {inc['title']}\n"
                f"Service: {inc['service_name']}\n"
                f"Severity: {inc['severity']}\n"
                f"Description: {inc['description'][:200]}...\n"
                f"Status: {inc['status']}"
                for inc in historical_incidents[:20]  # Limit to 20 for context
            ])
            
            prompt = f"""You are an expert incident analyst for a banking system.

Current Incident:
Title: {title}
Service: {service_name}
Description: {description}
Exception: {exception_text or 'N/A'}

Historical Resolved/Closed Incidents from the same bank:
{incidents_context}

Tasks:
1. Identify up to 5 most similar incidents from the historical list based on:
   - Service name
   - Error patterns
   - Exception traces
   - Problem description
   
2. For each similar incident, explain WHY it's similar (1-2 sentences)

3. Provide a brief recommendation (2-3 sentences) based on historical resolutions

Response format (JSON):
{{
    "similar_incident_ids": [id1, id2, ...],
    "similarity_reasons": {{
        "id1": "reason why incident 1 is similar",
        "id2": "reason why incident 2 is similar"
    }},
    "recommendation": "Your advisory recommendation text here"
}}
"""
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Try to parse JSON from response
            # Sometimes AI wraps in ```json ... ```
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            return {
                "similar_incidents": result.get("similar_incident_ids", []),
                "similarity_reasons": result.get("similarity_reasons", {}),
                "recommendation_text": result.get("recommendation", "No recommendation provided")
            }
            
        except Exception as e:
            print(f"AI error: {str(e)}")
            return {
                "similar_incidents": [],
                "similarity_reasons": {},
                "recommendation_text": f"AI analysis failed: {str(e)}"
            }
    
    def generate_bank_report(
        self,
        bank_name: str,
        incidents: List[Dict[str, Any]],
        summary_stats: Dict[str, Any]
    ) -> str:
        """
        Generate executive HTML report for a bank
        """
        if not self.enabled:
            return self._generate_fallback_bank_report(bank_name, incidents, summary_stats)
        
        try:
            incidents_summary = "\n".join([
                f"- #{inc['id']}: {inc['severity']} - {inc['title']} ({inc['status']})"
                for inc in incidents[:50]  # Limit for context
            ])
            
            prompt = f"""Generate an executive HTML report for {bank_name}'s incident management.

Statistics:
- Total Incidents: {summary_stats.get('total', 0)}
- Open: {summary_stats.get('open', 0)}
- In Progress: {summary_stats.get('in_progress', 0)}
- Resolved: {summary_stats.get('resolved', 0)}
- Closed: {summary_stats.get('closed', 0)}
- P1 (Critical): {summary_stats.get('p1', 0)}
- P2 (High): {summary_stats.get('p2', 0)}
- P3 (Medium): {summary_stats.get('p3', 0)}
- P4 (Low): {summary_stats.get('p4', 0)}

Recent Incidents:
{incidents_summary}

Create a professional, clean HTML report with:
1. Executive summary
2. Key metrics and trends
3. Top concerns and recommendations
4. Status breakdown with visual emphasis
5. Use professional banking colors (blues, grays)
6. Include proper HTML structure with embedded CSS
7. Make it print-friendly

Return ONLY the HTML code, no explanation.
"""
            
            response = self.model.generate_content(prompt)
            html = response.text.strip()
            
            # Clean up markdown code blocks if present
            if "```html" in html:
                html = html.split("```html")[1].split("```")[0].strip()
            elif "```" in html:
                html = html.split("```")[1].split("```")[0].strip()
            
            return html
            
        except Exception as e:
            print(f"AI report generation error: {str(e)}")
            return self._generate_fallback_bank_report(bank_name, incidents, summary_stats)
    
    def generate_incident_report(self, incident: Dict[str, Any]) -> str:
        """
        Generate detailed HTML report for a specific incident
        """
        if not self.enabled:
            return self._generate_fallback_incident_report(incident)
        
        try:
            prompt = f"""Generate a detailed executive HTML report for this incident:

Incident #{incident['id']}
Title: {incident['title']}
Severity: {incident['severity']}
Status: {incident['status']}
Service: {incident['service_name']}
Description: {incident['description']}
Created: {incident['created_at']}

Create a professional incident report with:
1. Incident overview
2. Timeline and status
3. Impact assessment
4. Current status and next steps
5. Use professional banking colors
6. Include proper HTML with embedded CSS
7. Make it print-friendly

Return ONLY the HTML code, no explanation.
"""
            
            response = self.model.generate_content(prompt)
            html = response.text.strip()
            
            if "```html" in html:
                html = html.split("```html")[1].split("```")[0].strip()
            elif "```" in html:
                html = html.split("```")[1].split("```")[0].strip()
            
            return html
            
        except Exception as e:
            print(f"AI incident report error: {str(e)}")
            return self._generate_fallback_incident_report(incident)
    
    def _generate_fallback_bank_report(
        self, bank_name: str, incidents: List[Dict], stats: Dict
    ) -> str:
        """Fallback HTML report without AI"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; color: #333; }}
        h1 {{ color: #0066cc; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 30px 0; }}
        .stat-box {{ background: #f5f5f5; padding: 20px; border-left: 4px solid #0066cc; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #0066cc; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #0066cc; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>{bank_name} - Incident Management Report</h1>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{stats.get('total', 0)}</div>
            <div>Total Incidents</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{stats.get('open', 0)}</div>
            <div>Open</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{stats.get('resolved', 0)}</div>
            <div>Resolved</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{stats.get('p1', 0)}</div>
            <div>Critical (P1)</div>
        </div>
    </div>
    
    <h2>Recent Incidents</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Severity</th>
            <th>Status</th>
        </tr>
        {''.join([f"<tr><td>#{i['id']}</td><td>{i['title']}</td><td>{i['severity']}</td><td>{i['status']}</td></tr>" for i in incidents[:20]])}
    </table>
</body>
</html>
"""
    
    def _generate_fallback_incident_report(self, incident: Dict) -> str:
        """Fallback incident report without AI"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; color: #333; }}
        h1 {{ color: #0066cc; }}
        .section {{ margin: 30px 0; padding: 20px; background: #f5f5f5; border-left: 4px solid #0066cc; }}
        .label {{ font-weight: bold; color: #0066cc; }}
    </style>
</head>
<body>
    <h1>Incident Report #{incident['id']}</h1>
    
    <div class="section">
        <p><span class="label">Title:</span> {incident['title']}</p>
        <p><span class="label">Severity:</span> {incident['severity']}</p>
        <p><span class="label">Status:</span> {incident['status']}</p>
        <p><span class="label">Service:</span> {incident['service_name']}</p>
        <p><span class="label">Created:</span> {incident['created_at']}</p>
    </div>
    
    <div class="section">
        <p class="label">Description:</p>
        <p>{incident['description']}</p>
    </div>
</body>
</html>
"""

# Global AI service instance
ai_service = AIService()
