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
            model_name="models/gemini-1.5-flash", 
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )

    def _verify_and_correct(self, candidate_translation, original_english):
        """
        Secondary pass to enforce Dutch linguistic rules:
        - Compound words (Samengestelde woorden)
        - Koppelteken for omission (Weglatingsstreepje)
        - Word order (V2, SOV)
        - Capitalization
        """
        verify_prompt = f"""
Role: Dutch Language Editor.
Task: Review and correct the following translation.

Original English: "{original_english}"
Candidate Dutch: "{candidate_translation}"

CHECKLIST:
1. **Capitalization (STRICT)**: MIRROR English casing EXACTLY. (e.g. "feedback" -> "feedback", "Feedback" -> "Feedback"). Do NOT capitalize nouns mid-sentence.
2. **Branding (INVIOLABLE)**: Ensure 'Driver-i' is NEVER translated to 'Bestuurder-i'. It must remain 'Driver-i'.
3. **Compound Words**: Are nouns combined? (e.g. 'Account Meldingen' -> 'Accountmeldingen').
4. **Variables**: Are `{{count}}` or `[text]` placeholders correctly placed?
5. **Ellipsis**: Is the hyphen used correctly? (e.g. 'Bestuurders- en Voertuiggroepen').

EXAMPLES OF CORRECTIONS:
- Input: "Bestuurders en Voertuiggroepen" -> Output: "Bestuurders- en Voertuiggroepen"
- Input: "Hallo, ik ben Bestuurder-i Assistent" -> Output: "Hallo, ik ben de Driver-i-assistent"
- Input: "Beschrijf uw Feedback" (Source: "Describe your feedback") -> Output: "Beschrijf uw feedback"
- Input: "Meer pagina's toevoegen" (Source: "Add More Pages") -> Output: "Meer Pagina's Toevoegen"

Instruction:
- If the Candidate Dutch is perfect, output it exactly.
- If errors exist, output ONLY the corrected Dutch version.
- Do NOT provide explanations. Just the text.
"""
        try:
            response = self.model.generate_content(verify_prompt)
            return response.text.strip()
        except:
            return candidate_translation
    
    def fix_utf8_mojibake(self, text):
        """
        Repairs common UTF-8 encoding errors (Mojibake).
        Specifically targets Windows-1252 artifacting.
        """
        if not isinstance(text, str):
            return str(text)
        
        replacements = {
            "Ã¢â‚¬Â¢": "•",  # Bullet (Standard encoding error)
            "â€¢": "•",      # Bullet (alt)
            "Ã¢": "â",       # Partial artifact
            "â¢": "•",       # Screenshot variant
            "Ã©": "é",       # e acute
            "Ã": "à",        # a grave (partial) - be careful here, usually context dependent
            "â€™": "'",      # Smart quote
            "â€œ": '"',      # Smart open quote
            "â€": '"',       # Smart close quote
            "Ã«": "ë",       # e diaeresis
            "Ã¯": "ï",       # i diaeresis
            "â€“": "-",      # En dash
        }
        
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    def _post_process_enforcement(self, dutch_text, source_english):
        """
        The 'Iron Fist' post-processor. 
        Forces formatting rules using Regex/Python overriding the LLM.
        """
        if not dutch_text: return ""
        
        # 1. BRANDING: Force "Driver-i" (Kill 'Bestuurder-i', 'Bestuurder i', 'Bestuurderi')
        # Regex matches: Bestuurder followed by optional dash/space and 'i' (case insensitive)
        branding_regex = r"(?i)\bbestuurder[-\s]*i\b"
        dutch_text = re.sub(branding_regex, "Driver-i", dutch_text)
        
        # 1.5. BRANDING: Ensure 'Driver-i' has an article if it looks like a noun phrase being introduced
        # "Ik ben Driver-i" -> "Ik ben de Driver-i"
        # We look for "ben Driver-i" or "is Driver-i" without "de"
        dutch_text = re.sub(r"(?i)\b(ben|is)\s+Driver-i\b", r"\1 de Driver-i", dutch_text)

        # 2. CASING: Mirror Source strictly for shared words
        # If English has "feedback" (lower) and Dutch has "Feedback" (Title), force lower.
        source_words = set(re.findall(r'\b[a-z]{4,}\b', source_english)) # strict lowercase words >3 chars
        
        def casing_fixer(match):
            word = match.group(0)
            lower_word = word.lower()
            # If the exact word exists in lowercase in source, FORCE lowercase in target
            if lower_word in source_words and word[0].isupper():
                return lower_word
            return word

        # Iterate over Dutch words and apply fixer
        # careful not to lowerStart of sentence? 
        # Actually, user wants "Beschrijf uw Feedback" -> "Beschrijf uw feedback". 
        # So yes, even Title cased words should be lowered if source is lower.
        dutch_text = re.sub(r'\b[A-Za-z]+\b', casing_fixer, dutch_text)

        return dutch_text

    def clean_text_for_prompt(self, text):
        if not isinstance(text, str):
            return str(text)
        
        # 1. Fix encoding first
        text = self.fix_utf8_mojibake(text)
        
        # 2. Normalize whitespace
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
3. Rephrase 'Input Text' to be grammatically correct (improved_english). **CRITICAL: Add missing articles (the, a) if the source sounds broken (e.g. "I am Driver-i" -> "I am THE Driver-i").**
4. Translate to Dutch using the Glossary (dutch_translation).

LINGUISTIC RULES (CRITICAL):
- **BRANDING (INVIOLABLE)**: NEVER translate 'Driver-i'. It is ALWAYS 'Driver-i', never 'Bestuurder-i'.
- **PUNCTUATION**: You MAY add commas or semicolons if it improves natural Dutch flow/readability.
- **CAPITALIZATION (STRICT)**: MIRROR English casing EXACTLY.
    - If English is "feedback" (lowercase), Dutch MUST be "feedback" (lowercase).
    - If English is "Feedback" (Title), Dutch MUST be "Feedback".
    - DO NOT capitalize nouns mid-sentence (German style) unless they are capitalized in English.
- **Compound Words**: ALWAYS combine nouns in Dutch. (e.g., 'Account Meldingen' -> 'Accountmeldingen').
- **Word Order**: Use natural Dutch syntax (SOV).
- **Ellipsis**: Use 'koppelteken' correctly (e.g., 'Bestuurders- en Voertuiggroepen').

GLOSSARY:
{glossary_text}

EXAMPLES:
{reference_examples}

Input Text: "{safe_json_source}"
"""
        retries = 3
        last_error = None
        
        for attempt in range(retries):
            try:
                # Exponential backoff for rate limits
                if attempt > 0:
                    time.sleep(2 ** attempt)
                    
                response = self.model.generate_content(prompt_json)
                if not response.parts:
                    raise ValueError("Blocked by safety filters or empty response")
                
                txt = response.text.strip()
                if "```" in txt:
                    txt = re.sub(r"```json\s*", "", txt, flags=re.IGNORECASE).replace("```", "")
                
                # Sanitize newlines inside JSON strings if they break parsing
                # (Simple approach: assume strict JSON structure from model)
                
                data = json.loads(txt)
                
                if "improved_english" not in data or "dutch_translation" not in data:
                    raise ValueError("Missing JSON keys")
                
                # --- VERIFICATION STEP (New) ---
                verified_dutch = self._verify_and_correct(data["dutch_translation"], source_text)

                # --- POST-PROCESSING ENFORCEMENT ---
                final_dutch = self._post_process_enforcement(verified_dutch, source_text)

                # --- ALL CAPS ENFORCEMENT ---
                if source_text.isupper() and len(source_text) > 1:
                    data["improved_english"] = data["improved_english"].upper()
                    final_dutch = final_dutch.upper()

                return {
                    "original_english": source_text,
                    "improved_english": data["improved_english"],
                    "dutch_translation": final_dutch
                }
            except Exception as e:
                last_error = e
                # If it's a 429/ResourceExhausted, we really want to retry/wait
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                    time.sleep(5) # Extra wait for quota
                continue

        # --- STRATEGY B: Fallback Text-Only ---
        # If we are here, Strategy A failed all retries.
        
        prompt_text = f"""
Role: Technical Translator (English -> Dutch).
Task: Translate the following English text to Dutch.
Use these terms if present: {glossary_text}

Input: "{clean_noline_source}"

Return ONLY the Dutch translation. do not include any other text.
"""
        try:
            # Short pause before fallback attempt
            time.sleep(1)
            response = self.model.generate_content(prompt_text)
            dutch_text = response.text.strip()
            
            final_dutch = self._post_process_enforcement(dutch_text, source_text)

            if source_text.isupper() and len(source_text) > 1:
                clean_noline_source = clean_noline_source.upper()
                final_dutch = final_dutch.upper()
            
            return {
                "original_english": source_text,
                "improved_english": clean_noline_source,
                "dutch_translation": final_dutch
            }
        except Exception as e:
            # FINAL FAIL
            error_msg = f"ERROR: {str(e)}"
            if last_error:
               error_msg += f" | JSON Error: {str(last_error)}"
               
            return {
                "original_english": source_text,
                "improved_english": error_msg[:1000],  # Limit length
                "dutch_translation": "ERROR_FAILED"
            }

    @staticmethod
    def build_glossary_dict(df_glossary):
        if df_glossary is None or df_glossary.empty: return {}
        
        term_col = next((c for c in df_glossary.columns if 'term' in c.lower()), None)
        trans_col = next((c for c in df_glossary.columns if 'translation_nl' in c.lower() or 'dutch' in c.lower()), None)
        
        if not term_col or not trans_col:
            return {}
            
        # Clean Data: Drop NaNs and ensure strings
        df_clean = df_glossary.dropna(subset=[term_col, trans_col]).copy()
        df_clean[term_col] = df_clean[term_col].astype(str).str.strip()
        df_clean[trans_col] = df_clean[trans_col].astype(str).str.strip()
        
        # Filter out empty strings or literal "nan" strings just in case
        df_clean = df_clean[df_clean[term_col].str.lower() != 'nan']
        df_clean = df_clean[df_clean[trans_col].str.lower() != 'nan']
        df_clean = df_clean[df_clean[term_col] != '']

        return df_clean.set_index(term_col)[trans_col].to_dict()

    @staticmethod
    def find_relevant_terms(text, glossary_dict):
        if not isinstance(text, str): return ""
        text_lower = text.lower()
        found = []
        for term, trans in glossary_dict.items():
            if str(term).lower() in text_lower:
                found.append(f"- '{term}' -> '{trans}'")
        return "\n".join(found[:15])
