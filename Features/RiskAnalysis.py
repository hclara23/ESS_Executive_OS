from datetime import datetime
from Features.MemoryStore import add_private_memory
from Features.Face.Mouth import speak

def analyze_project_risk(user: str, project_name: str) -> str:
    """
    Simulates predictive delay & risk analysis based on weather, materials, and schedule.
    """
    speak(f"Running predictive risk analysis for the {project_name} project.")
    
    # Mock Risk factors
    weather_risk = "High - Heavy rain forecasted for next week."
    material_risk = "Medium - Switchgear delivery delayed by 4 days."
    financial_risk = "Low - Budget is currently running 2% under."
    
    # Synthesis
    summary = f"Risk Analysis for {project_name}:\\n- Weather: {weather_risk}\\n- Materials: {material_risk}\\n- Financials: {financial_risk}\\nOverall Prediction: Potential 4-day schedule delay. Recommend shifting flatwork to this week."
    
    speak("I have calculated the project risks.")
    add_private_memory(user, f"Risk Analysis generated for {project_name}: Potential 4-day delay.", tags=["risk", "prediction", "project"])
    
    return summary
