from openai import OpenAI
import base64
import json
import streamlit as st
from PIL import Image, ImageEnhance
import io

google_api_key = st.secrets["GOOGLE_API_KEY"]
gemini_via_openai_client = OpenAI(
    api_key=google_api_key, 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
system_prompt = """
here's picture of a restaurant check (probobly in hebrew). 
Extract items from Hebrew restaurant receipt image. Return a list of dictionaries with:
name:(string), try to find the most possible item menu based on the OCR. in the origin languege, if you think this is a side dish please add this to the name (if it doesn't have a quntity or indented)
quantity: integer. Use multiplier (e.g. x3) or infer from repeated lines. Side dishes/comments inherit quantity from item above. Items may be sold by weight, partial quantities will be converted to quantity 1 .
total_price: float. Normalize (no currency symbols, commas, etc.). do not include if equal 0
price_per_unit: float = total_price ÷ quantity.
Match prices to items logically. Ignore subtotal, tax, tip unless itemized. make sure every item that have a price is recognized
Output rules: - Return strictly a JSON-like Python list of dictionaries. - Do not include any extra text, explanations, or formatting outside the list.
"""

def get_menu_items(uploaded_image):
    img = Image.open(uploaded_image)

    bw = img.convert("L")  
    contrast_enhancer = ImageEnhance.Contrast(bw)
    bw_contrast = contrast_enhancer.enhance(3.0)
    brighness_enhancer = ImageEnhance.Brightness(bw_contrast)
    bw_contrast_br = brighness_enhancer.enhance(2.0) 
    sharpness_enhancer = ImageEnhance.Sharpness(bw_contrast_br)
    final_img = sharpness_enhancer.enhance(2.0)  
    buffered = io.BytesIO()
    final_img.save(buffered, format="PNG")
    b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")

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
                        "text": "what are the items in this restaurant bill?"
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

    try:
        cleaned_json = response.choices[0].message.content.strip("`json\n").strip("`")
        return json.loads(cleaned_json)
    except Exception as e:
        raise e

