import os
import base64
from dotenv import load_dotenv
from server.ai_provider import chat_completion

load_dotenv()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_with_vision(image_path, prompt):
    """
    Uses GPT-4o Vision to analyze an image (local path).
    """
    if not os.path.exists(image_path):
        return f"Error: Image path {image_path} does not exist."
        
    base64_image = encode_image(image_path)
    
    try:
        response = chat_completion(
            "vision",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
            temperature=0.1,
        )
        result = response.choices[0].message.content
        
        # Phase 2: Autonomous Compliance Audit
        try:
            from Features.ComplianceSentinel import compliance_sentinel
            compliance_sentinel.audit_visual_stream(result)
        except Exception as ex:
            print(f"Compliance audit failed: {ex}")
            
        return result
    except Exception as e:
        return f"Vision Analysis Error: {str(e)}"
