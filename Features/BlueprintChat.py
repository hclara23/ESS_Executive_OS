from Features.MemoryStore import add_private_memory
from Features.TechIntel import search_code_compliance
from Features.Face.Mouth import speak
from Features.Vision import analyze_image_with_vision

def analyze_blueprint(user: str, query: str, image_path: str = None) -> str:
    """
    Analyzes a CAD/BIM PDF (or image) using GPT-4o Vision and checks NEC/OSHA codes.
    """
    speak("Analyzing the blueprint with Vision AI.")
    
    if not image_path:
        return "No blueprint image provided for analysis."

    prompt = f"Analyze this blueprint image. Specifically look for: {query}. Identify any potential code violations or technical issues."
    
    # Real Vision AI processing
    analysis_result = analyze_image_with_vision(image_path, prompt)
    
    # Check compliance using existing TechIntel for agentic verification
    compliance_info = search_code_compliance(query)
    
    final_summary = f"Blueprint Vision Analysis: {analysis_result}\n\nTechnical Code Reference: {compliance_info}"
    speak("I have finished the real-time analysis.")
    add_private_memory(user, f"Analyzed blueprint regarding '{query}': {final_summary}", tags=["blueprint", "engineering"])
    return final_summary

