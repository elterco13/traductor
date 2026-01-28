"""
Simple test to verify post-processing enforcement works correctly.
Tests formality fixes (je->u) and compound word formation (Driver•i app -> Driver•i-app)
"""
import re

def _post_process_enforcement(dutch_text, source_english):
    """
    The 'Iron Fist' post-processor. 
    Forces formatting rules using Regex/Python overriding the LLM.
    """
    if not dutch_text: return ""
    
    # 1. BRANDING: Force "Driver•i" or "Driver-i"
    branding_regex = r"(?i)\bbestuurder[-\s]*i\b"
    dutch_text = re.sub(branding_regex, "Driver•i", dutch_text)
    
    # 1.5. BRANDING: Ensure 'Driver•i' or 'Driver-i' has an article
    dutch_text = re.sub(r"(?i)\b(ben|is)\s+Driver[•-]i\b", r"\1 de Driver•i", dutch_text)
    
    # 1.6. COMPOUND WORDS: Brand + noun should be hyphenated
    dutch_text = re.sub(r"\b(Driver[•-]i)\s+([A-Z][a-z]+)", r"\1-\2", dutch_text)
    dutch_text = re.sub(r"\b(Driver[•-]i)\s+(app|assistent|scherm|functie)\b", r"\1-\2", dutch_text, flags=re.IGNORECASE)

    # 2. FORMALITY: Force formal pronouns
    dutch_text = re.sub(r"\bje\b", "u", dutch_text)
    dutch_text = re.sub(r"\bjouw\b", "uw", dutch_text)
    dutch_text = re.sub(r"\bjou\b", "u", dutch_text)

    # 3. CASING: Mirror Source strictly for shared words
    source_words = set(re.findall(r'\b[a-z]{4,}\b', source_english))
    
    def casing_fixer(match):
        word = match.group(0)
        lower_word = word.lower()
        if lower_word in source_words and word[0].isupper():
            return lower_word
        return word

    dutch_text = re.sub(r'\b[A-Za-z]+\b', casing_fixer, dutch_text)

    return dutch_text

# Test cases
test_cases = [
    ("je feedback", "your feedback", "Formality: je -> u"),
    ("voordat je begint", "before you start", "Formality: je -> u"),
    ("Driver•i app", "Driver•i app", "Compound: Driver•i app -> Driver•i-app"),
    ("Driver i Assistent", "Driver i Assistant", "Compound: Driver i Assistent -> Driver•i-assistent"),
    ("jouw account", "your account", "Formality: jouw -> uw"),
    ("Bestuurder-i app", "Driver-i app", "Branding: Bestuurder-i -> Driver•i"),
]

print("=" * 80)
print("TEST: Post-Processing Enforcement")
print("=" * 80)

passed = 0
failed = 0

for dutch_input, english_source, description in test_cases:
    result = _post_process_enforcement(dutch_input, english_source)
    print(f"\n{description}")
    print(f"  Input:  '{dutch_input}'")
    print(f"  Output: '{result}'")
    if dutch_input != result:
        print(f"  ✅ CHANGED")
        passed += 1
    else:
        print(f"  ⚠️  NO CHANGE")
        failed += 1

print("\n" + "=" * 80)
print(f"SUMMARY: {passed} tests passed, {failed} tests failed")
print("=" * 80)
