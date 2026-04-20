import os
import json
import base64
from dotenv import load_dotenv
from server.ai_provider import chat_completion

def process_receipt_image(image_path):
    """
    Uses GPT-4o Vision to extract data from a receipt and categorize it for tax purposes.
    """
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    prompt = """
    Analyze this receipt image and extract the following information in valid JSON format:
    {
      "vendor": "Name of the store or service",
      "total_amount": 0.00,
      "tax_amount": 0.00,
      "category": "Tax category (e.g., Office Supplies, Travel, Meals, Tools, Software, Hardware, Advertising, Utilities)",
      "items": [
        {"name": "Item Name", "price": 0.00}
      ]
    }
    
    Ensure the response is ONLY the JSON object.
    """

    try:
        response = chat_completion(
            "receipt_vision",
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
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Receipt Vision Error: {e}")
        return None
