from openai import OpenAI
import base64
import json
import streamlit as st

google_api_key = st.secrets["GOOGLE_API_KEY"]
gemini_via_openai_client = OpenAI(
    api_key=google_api_key, 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
system_prompt = """
here's picture of a restaurant check (probobly in hebrew). 
Extract items from Hebrew restaurant receipt image. Return a list of dictionaries with:
name:(string), try to find the most possible item menu based on the OCR. in the origin languege, if you think this is a side dish please add this to the name (if it doesn't have a quntity or indented)
quantity: integer. Use multiplier (e.g. x3) or infer from repeated lines. Side dishes/comments inherit quantity from item above.
total_price: float. Normalize (no currency symbols, commas, etc.). do not include if equal 0
price_per_unit: float = total_price ÷ quantity.
Match prices to items logically. Ignore subtotal, tax, tip unless itemized.
Output rules: - Return strictly a JSON-like Python list of dictionaries. - Do not include any extra text, explanations, or formatting outside the list.
"""
def get_menu_items(uploaded_image):
    # Read image bytes from the uploaded file
    b64_img = base64.b64encode(uploaded_image.read()).decode("utf-8")

    # Send image and prompt to OpenAI
    response = gemini_via_openai_client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "what are the items in this resturant bill?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64_img}"
                        }
                    }
                ]
            }
        ]
    )
    
    cleaned_json = response.choices[0].message.content.strip("`json\n").strip("`")
    # Parse into Python list
    return json.loads(cleaned_json) 