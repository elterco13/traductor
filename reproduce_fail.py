import google.generativeai as genai
import os
import json
import re

API_KEY = "AIzaSyBnxCZyROPkB3ijicG5iEB4twI7pgY3AI4"
genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash", 
    generation_config=generation_config,
    safety_settings=safety_settings
)

# failing text
text = "Privacy Mode is disabled as soon as\n the vehicle ignition is on and the vehicle\n speed reaches 5 mph or more."
safe_text = text.replace('"', '\\"').replace('\n', ' ')

prompt = f"""
Role: Expert Technical Translator (English to Dutch).
Task: Process the input English text and translate it to Dutch.

Input Text: "{safe_text}"

Output Format:
Return a raw JSON object (no markdown formatting) with these keys:
{{
  "original_english": "{safe_text}",
  "improved_english": "...",
  "dutch_translation": "..."
}}
"""

print(f"Testing text: {safe_text}")

try:
    response = model.generate_content(prompt)
    print("--- RESPONSE ---")
    print(response.text)
    print("----------------")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Feedback: {e.response.prompt_feedback}")
