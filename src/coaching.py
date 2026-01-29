"""
Optional LLM coaching module for behavioral insights.
This module is optional and does not affect deterministic violation detection.
"""
from typing import List, Dict, Optional
from .schemas import Violation


def generate_coaching_summary(
    violations: List[Violation],
    violation_summary: Dict[str, int],
    compliance_score: float
) -> Optional[str]:
    """
    Generate a behavioral coaching summary using LLM.
    
    Args:
        violations: List of violation objects
        violation_summary: Dictionary of violation types and counts
        compliance_score: Current compliance score (0.0-1.0)
    
    Returns:
        Coaching summary string or None if LLM call fails
    """
    try:
        import openai
    except ImportError:
        return None
    
    # Check if OpenAI API key is set
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        # Prepare violation context for LLM
        violation_types = list(violation_summary.keys())
        violation_counts = list(violation_summary.values())
        
        # Create summary text
        summary_text = f"Compliance Score: {compliance_score:.2f}\n"
        summary_text += f"Violation Types: {', '.join(violation_types)}\n"
        summary_text += f"Violation Counts: {', '.join(map(str, violation_counts))}\n\n"
        summary_text += "Violations:\n"
        for v in violations[:10]:  # Limit to first 10 for context
            summary_text += f"- {v.violation_type}: {v.detail}\n"
        
        # Call OpenAI API
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cost-effective model
            messages=[
                {
                    "role": "system",
                    "content": "You are a trading discipline coach. Analyze violations and provide a single paragraph of behavioral coaching focused on improving trading discipline. Be specific, actionable, and encouraging."
                },
                {
                    "role": "user",
                    "content": f"Analyze these trading discipline violations and provide coaching:\n\n{summary_text}"
                }
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        coaching_summary = response.choices[0].message.content.strip()
        return coaching_summary
        
    except Exception:
        # Silently fail - this is optional functionality
        return None
