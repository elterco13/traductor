import pandas as pd
import requests
import google.generativeai as genai
import time
import json
import io
import os
import re
import sys

# Force UTF-8 environment logic
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

class TranslatorBackend:
    def __init__(self, api_key):
        self.api_key = api_key
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.generation_config = {
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        self.model = genai.GenerativeModel(
            model_name="models/gemini-2.5-flash", 
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
    
    def clean_text_for_prompt(self, text):
        if not isinstance(text, str):
            return str(text)
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def translate_row_robust(self, source_text, glossary_text, reference_examples=""):
        clean_noline_source = self.clean_text_for_prompt(source_text)
        safe_json_source = clean_noline_source.replace('"', '\\"')
        
        # --- STRATEGY A: Strict JSON ---
        prompt_json = f"""
You are an expert technical translator converting English to Dutch.

STRICT INSTRUCTIONS:
1. Output JSON ONLY. No markdown.
2. Structure: {{ "original_english": "...", "improved_english": "...", "dutch_translation": "..." }}
3. Rephrase 'Input Text' to be grammatically correct (improved_english).
4. Translate to Dutch using the Glossary (dutch_translation).

GLOSSARY:
{glossary_text}

EXAMPLES:
{reference_examples}

Input Text: "{safe_json_source}"
"""
        retries = 2
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt_json)
                if not response.parts:
                    raise ValueError("Empty response")
                
                txt = response.text.strip()
                if "```" in txt:
                    txt = re.sub(r"```json\s*", "", txt, flags=re.IGNORECASE).replace("```", "")
                
                data = json.loads(txt)
                
                if "improved_english" not in data or "dutch_translation" not in data:
                    raise ValueError("Missing JSON keys")
                    
                return {
                    "original_english": source_text,
                    "improved_english": data["improved_english"],
                    "dutch_translation": data["dutch_translation"]
                }
            except Exception as e:
                time.sleep(1)

        # --- STRATEGY B: Fallback Text-Only ---
        prompt_text = f"""
Role: Technical Translator (English -> Dutch).
Task: Translate the following English text to Dutch.
Use these terms if present: {glossary_text}

Input: "{clean_noline_source}"

Return ONLY the Dutch translation. do not include any other text.
"""
        try:
            response = self.model.generate_content(prompt_text)
            dutch_text = response.text.strip()
            return {
                "original_english": source_text,
                "improved_english": clean_noline_source,
                "dutch_translation": dutch_text
            }
        except Exception as e:
            return {
                "original_english": source_text,
                "improved_english": "ERROR_FAILED",
                "dutch_translation": ""
            }

    @staticmethod
    def build_glossary_dict(df_glossary):
        if df_glossary is None or df_glossary.empty: return {}
        # normalize columns if needed, but assuming standard format
        # Check standard cols
        term_col = next((c for c in df_glossary.columns if 'term' in c.lower()), None)
        trans_col = next((c for c in df_glossary.columns if 'translation_nl' in c.lower() or 'dutch' in c.lower()), None)
        
        if not term_col or not trans_col:
            return {}
            
        return df_glossary.set_index(term_col)[trans_col].to_dict()

    @staticmethod
    def find_relevant_terms(text, glossary_dict):
        if not isinstance(text, str): return ""
        text_lower = text.lower()
        found = []
        for term, trans in glossary_dict.items():
            if str(term).lower() in text_lower:
                found.append(f"- '{term}' -> '{trans}'")
        return "\n".join(found[:15])
