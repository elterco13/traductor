import google.generativeai as genai
import os

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
    model_name="models/gemini-2.5-pro", 
    generation_config=generation_config,
    safety_settings=safety_settings
)

text = "Hi in this video, let us learn\n about Privacy Mode in detail."
glossary = "- 'Privacy Mode' -> 'Privacymodus'"

prompt = f"""
Role: Expert Technical Translator (English to Dutch).
Task: Process the input English text and translate it to Dutch.

Input Text: "{text.replace('\n', ' ')}"

Glossary Terms (Must Use if applicable):
{glossary}

Instructions:
1. IMPROVE ENGLISH: Rephrase logically.
2. TRANSLATE: Translate improved English to Dutch.

Output Format:
Return a raw JSON object (no markdown formatting) with these keys:
{{
  "original_english": "...",
  "improved_english": "...",
  "dutch_translation": "..."
}}
"""

print(f"Testing model: {model.model_name}")
try:
    response = model.generate_content(prompt)
    print("Response parts:", response.parts)
    print("Response text:", response.text)
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Feedback: {e.response.prompt_feedback}")
