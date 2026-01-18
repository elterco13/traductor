import pandas as pd
import requests
import google.generativeai as genai
import time
import json
import io
import os
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION
# CONFIGURATION
# SECURITY NOTE: Never hardcode API keys in production scripts.
API_KEY = os.getenv("GOOGLE_API_KEY") 
if not API_KEY:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")
DOC_URL = "https://docs.google.com/spreadsheets/d/1--ANBO4vxR2jMvwdoSOUGXWuZlR2RI3fFcUfWgzoxdc/export?format=csv"
GLOSSARY_URL = "https://docs.google.com/spreadsheets/d/1Au9OHt0wL1XTJgOEoJMgNpYcTe89v8w9TlaFcVc5kzY/export?format=csv"

OUTPUT_FILE = "TRANSLATION_RESULTS_V2.csv"

# Configure Gemini
genai.configure(api_key=API_KEY)
generation_config = {
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024,
}

# Critical: Adjust safety settings to avoid blocking technical content
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

def download_data(url, filename):
    print(f"Downloading data from {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # Save for reference
        with open(filename, 'wb') as f:
            f.write(response.content)
        return pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        # Fallback to local file if it exists
        if os.path.exists(filename):
            print(f"Falling back to local file {filename}...")
            return pd.read_csv(filename)
        raise

def build_glossary_dict(df_glossary):
    """
    Builds a list of dictionary entries for easier searching.
    """
    if 'term' not in df_glossary.columns or 'translation_nl' not in df_glossary.columns:
        print("Warning: Glossary columns mismatch. Expecting 'term' and 'translation_nl'.")
        print(f"Found: {df_glossary.columns}")
        return {}
    
    # Create a dictionary mapping term to translation_nl
    glossary_dict = df_glossary.set_index('term')['translation_nl'].to_dict()
    return glossary_dict

import re
import random
import sys
import argparse

# Force UTF-8 for stdout/stderr to avoid encoding crash on Windows consoles
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def clean_text_for_prompt(text):
    """
    Flattens text to a single line for safer JSON prompting.
    """
    if not isinstance(text, str):
        return str(text)
    # 1. Fix encoding first
    text = fix_utf8_mojibake(text)
    
    # 2. Normalize whitespace
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fix_utf8_mojibake(text):
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

def _verify_and_correct(candidate_translation, source_text):
    """
    Self-Correction Loop using the LLM.
    """
    verification_prompt = f"""
Role: Quality Assurance for English -> Dutch translation.
Task: Verify and correct the Dutch translation below.

Source English: "{source_text}"
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
- If the Candidate Dutch is perfect, output it EXACTLY as is.
- If there are errors, output the CORRECTED version only.
- Output ONLY the final Dutch string.
"""
    try:
        response = model.generate_content(verification_prompt)
        return response.text.strip()
    except Exception:
        return candidate_translation

def _post_process_enforcement(dutch_text, source_english):
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
    dutch_text = re.sub(r'\b[A-Za-z]+\b', casing_fixer, dutch_text)

    return dutch_text

def translate_row_robust(source_text, glossary_text, reference_examples=""):
    """
    Tries to translate using JSON mode first.
    If that fails, falls back to a simple Text-Only mode to ensure we get a result.
    """
    # 1. Prepare Prompt Inputs
    # We clean the text for the PROMPT (to avoid breaking JSON syntax in the prompt), 
    # but we store the original source in the output.
    clean_noline_source = clean_text_for_prompt(source_text)
    safe_json_source = clean_noline_source.replace('"', '\\"')
    
    # --- STRATEGY A: Strict JSON ---
    prompt_json = f"""
You are an expert technical translator converting English to Dutch.

STRICT INSTRUCTIONS:
1. Output JSON ONLY. No markdown.
2. Structure: {{ "original_english": "...", "improved_english": "...", "dutch_translation": "..." }}
3. Rephrase 'Input Text' to be grammatically correct (improved_english).
   - **CRITICAL:** Add missing articles (the, a) e.g. "I am Driver-i" -> "I am THE Driver-i".
   - **IMMUTABLE TERMS:** DO NOT change, split, or 'fix' the following terms in the English text: ['Driver•i', 'Driver-i', 'Netradyne']. Treat 'Driver•i' as a valid proper noun, NOT a typo.
4. Translate to Dutch using the Glossary (dutch_translation).

LINGUISTIC RULES (CRITICAL):
- **BRANDING (INVIOLABLE)**: NEVER translate 'Driver-i' or 'Driver•i'. It is ALWAYS 'Driver-i'/'Driver•i'.
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
    
    retries = 2
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt_json)
            if not response.parts:
                raise ValueError("Empty response / Safety Block")
            
            # Clean possible markdown format
            txt = response.text.strip()
            if "```" in txt:
                txt = re.sub(r"```json\s*", "", txt, flags=re.IGNORECASE).replace("```", "")
            
            # Try parse
            data = json.loads(txt)
            
            # Validate keys exist
            if "improved_english" not in data or "dutch_translation" not in data:
                raise ValueError("Missing JSON keys")
            
            # --- VERIFICATION STEP (New) ---
            verified_dutch = _verify_and_correct(data["dutch_translation"], source_text)

            # --- POST-PROCESSING ENFORCEMENT (The "Iron Fist") ---
            final_dutch = _post_process_enforcement(verified_dutch, source_text)
            
            # --- CRITICAL: ALL CAPS ENFORCEMENT ---
            # If source is 100% CAPS (and length > 1 to avoid 'A'), force output to be CAPS.
            if source_text.isupper() and len(source_text) > 1:
                data["improved_english"] = data["improved_english"].upper()
                final_dutch = final_dutch.upper()

            return {
                "original_english": source_text, # Keep original formatting in CSV
                "improved_english": data["improved_english"],
                "dutch_translation": final_dutch
            }
        except Exception as e:
            # print(f"    [Strategy A] Attempt {attempt+1} failed: {e}")
            time.sleep(1)

    # --- STRATEGY B: Fallback Text-Only ---
    # If JSON failed repeatedly, we just ask for the Dutch text directly.
    # We will fill 'improved_english' with a placeholder or just the clean source.
    print(f"    [!] Switches to Strategy B (Text fallback) for: {clean_noline_source[:30]}...")
    
    prompt_text = f"""
Role: Technical Translator (English -> Dutch).
Task: Translate the following English text to Dutch.
Use these terms if present: {glossary_text}

Input: "{clean_noline_source}"

Return ONLY the Dutch translation. do not include any other text.
"""
    try:
        response = model.generate_content(prompt_text)
        dutch_text = response.text.strip()
        # Even in fallback, apply Iron Fist
        final_dutch = _post_process_enforcement(dutch_text, source_text)
        
        # --- CRITICAL: ALL CAPS ENFORCEMENT ---
        if source_text.isupper() and len(source_text) > 1:
            clean_noline_source = clean_noline_source.upper()
            final_dutch = final_dutch.upper()
        
        return {
            "original_english": source_text,
            "improved_english": clean_noline_source, # Fallback: just use cleaned source
            "dutch_translation": final_dutch
        }
    except Exception as e:
        print(f"    [Strategy B] Failed: {e}")
        return {
            "original_english": source_text,
            "improved_english": "ERROR_FAILED",
            "dutch_translation": ""
        }

def find_relevant_terms(text, glossary_dict):
    """
    Simple keyword matching.
    """
    if not isinstance(text, str): return ""
    text_lower = text.lower()
    found = []
    for term, trans in glossary_dict.items():
        if term.lower() in text_lower: # Case-insensitive matching for terms
            found.append(f"- '{term}' -> '{trans}'")
    
    # Limit to top 15 terms to conserve context
    return "\n".join(found[:15])

def load_reference_examples(reference_path="reference_data.csv", n=5):
    """
    Loads random examples from the reference CSV to use as few-shot prompts.
    """
    if not os.path.exists(reference_path):
        return ""
    try:
        df = pd.read_csv(reference_path)
        if len(df) < n:
            sample = df
        else:
            sample = df.sample(n)
        
        examples_text = "\n".join([
            f"Input: \"{row.iloc[0]}\"\nOutput: {{ \"original_english\": \"{row.iloc[0]}\", \"improved_english\": \"{row.iloc[0]}\", \"dutch_translation\": \"{row.iloc[1]}\" }}"
            for _, row in sample.iterrows()
        ])
        return examples_text
    except Exception as e:
        print(f"Warning: Could not load reference examples: {e}")
        return ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair", action="store_true", help="Fix failed rows in existing results.")
    args = parser.parse_args()

    print("--- Starting Translation Process (Robust V3) ---")
    
    # 1. Download Data
    img_glossary_file = "glossary_data.csv"
    img_doc_file = "source_doc_data.csv"
    
    # Always refresh data
    df_glossary = download_data(GLOSSARY_URL, img_glossary_file)
    glossary_dict = build_glossary_dict(df_glossary)
    
    # Identify source column
    df_doc = download_data(DOC_URL, img_doc_file)
    source_col = next((c for c in df_doc.columns if 'source' in c.lower() or 'en_us' in c.lower()), df_doc.columns[0])
    print(f"Source Column: {source_col}")

    # 2. Repair Mode or Append Mode
    if args.repair:
        print(">>> REPAIR MODE ACTIVATED <<<")
        if not os.path.exists(OUTPUT_FILE):
            print("No output file to repair.")
            return
            
        df_results = pd.read_csv(OUTPUT_FILE)
        
        # Identify failed rows
        mask_fail = (df_results["improved_english"] == "ERROR_FAILED") | (df_results["dutch_translation"].isna())
        failed_indices = df_results[mask_fail].index
        
        print(f"Found {len(failed_indices)} rows to repair.")
        
        for idx in failed_indices:
            row_data = df_results.loc[idx]
            original_text = row_data["original_english"]
            
            print(f"Repairing Row {idx+1}...", end="\r")
            
            updated_row = translate_row_robust(
                original_text, 
                find_relevant_terms(original_text, glossary_dict),
                load_reference_examples("reference_data.csv", 3)
            )
            
            # Update output DF in memory
            df_results.at[idx, "improved_english"] = updated_row["improved_english"]
            df_results.at[idx, "dutch_translation"] = updated_row["dutch_translation"]
            
            # Save constantly to avoid data loss
            # For repair, overwriting the whole CSV is safer to keep order, 
            # but we can improve efficiency if needed. For now, simple rewrite is safe for 500 rows.
            if idx % 5 == 0: # Save batch
                 df_results.to_csv(OUTPUT_FILE, index=False)
            
            time.sleep(1.0)
            
        # Final Save
        df_results.to_csv(OUTPUT_FILE, index=False)
        print("\nRepair Complete.")
        
    else:
        # Standard Process (Append / Resume)
        print(">>> STANDARD MODE ACTIVATED <<<")
        if not os.path.exists(OUTPUT_FILE):
             pd.DataFrame(columns=["original_english", "improved_english", "dutch_translation"]).to_csv(OUTPUT_FILE, index=False)
             processed_count = 0
        else:
             existing_df = pd.read_csv(OUTPUT_FILE)
             processed_count = len(existing_df)
             print(f"Resuming from row {processed_count}...")
        
        rows_to_process = df_doc.iloc[processed_count:]
        total_rows = len(df_doc)

        for index, row in rows_to_process.iterrows():
            source_text = row[source_col]
            if pd.isna(source_text) or str(source_text).strip() == "":
                # Append an empty row to maintain alignment if resuming
                empty_result = {
                    "original_english": source_text,
                    "improved_english": "",
                    "dutch_translation": ""
                }
                pd.DataFrame([empty_result]).to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
                continue

            print(f"[{index+1}/{total_rows}] Processing...", end="\r")
            
            result = translate_row_robust(
                source_text,
                find_relevant_terms(source_text, glossary_dict),
                load_reference_examples("reference_data.csv", 3)
            )
            
            new_df = pd.DataFrame([result])
            new_df = new_df[["original_english", "improved_english", "dutch_translation"]]
            new_df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
            
            time.sleep(1.0)

    print(f"\nDone! Results saved to: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()
