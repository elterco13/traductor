import pandas as pd
import requests
import google.generativeai as genai
import time
import json
import io
import os
import sys
from dotenv import load_dotenv

# Import the translation function from the main script
sys.path.insert(0, os.path.dirname(__file__))
from translate_script import translate_row_robust, build_glossary_dict, download_data, GLOSSARY_URL

load_dotenv()

# Configure Gemini
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

print("=" * 80)
print("PRUEBA DE CALIDAD DE TRADUCCIÓN - Ejemplos Problemáticos")
print("=" * 80)

# Load glossary
print("\nCargando glosario...")
df_glossary = download_data(GLOSSARY_URL, "glossary_data.csv")
glossary_dict = build_glossary_dict(df_glossary)

# Test cases based on user's reported issues
test_cases = [
    {
        "name": "Test 1: Formalidad (je -> u)",
        "source": "Before you begin logging your duty status, ensure the following requirements are met:",
        "expected_issues": [
            "Debe usar 'u/uw' (formal), NO 'je/jouw' (informal)",
            "Cláusula subordinada debe estar en posición natural holandesa"
        ]
    },
    {
        "name": "Test 2: Glosario Driver•i",
        "source": "The Driver•i app helps you track your hours",
        "expected_issues": [
            "Debe mantener 'Driver•i' exactamente (no 'Driver.i' ni 'Driveri')",
            "Debe formar 'Driver•i-app' con guion"
        ]
    },
    {
        "name": "Test 3: Traduccionismo 'voor de dag'",
        "source": "The HoS screen in the Driver•i app allows you to confirm your active duty status for the day",
        "expected_issues": [
            "NO debe incluir 'voor de dag' (no existe en holandés)",
            "Debe usar 'u/uw' (formal)",
            "Debe formar 'Driver•i-app' correctamente"
        ]
    },
    {
        "name": "Test 4: Palabras compuestas",
        "source": "Account Notifications and Vehicle Groups",
        "expected_issues": [
            "Debe formar 'Accountmeldingen' (sin espacio)",
            "Debe formar 'Voertuiggroepen' (sin espacio)",
            "Debe usar elipsis con guion: 'Account- en Voertuiggroepen' o separado"
        ]
    },
    {
        "name": "Test 5: Orden de palabras natural",
        "source": "Before you start, make sure all requirements are met",
        "expected_issues": [
            "Debe usar orden natural holandés, no calco del inglés",
            "Debe usar 'u' (formal)"
        ]
    }
]

print("\n" + "=" * 80)
print("EJECUTANDO PRUEBAS")
print("=" * 80)

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n{'─' * 80}")
    print(f"🔍 {test['name']}")
    print(f"{'─' * 80}")
    print(f"📝 Inglés original:")
    print(f"   {test['source']}")
    print(f"\n⚠️  Problemas a verificar:")
    for issue in test['expected_issues']:
        print(f"   • {issue}")
    
    print(f"\n⏳ Traduciendo...")
    
    # Find relevant glossary terms
    glossary_text = ""
    for term, trans in glossary_dict.items():
        if term.lower() in test['source'].lower():
            glossary_text += f"- '{term}' -> '{trans}'\n"
    
    # Translate
    result = translate_row_robust(
        test['source'],
        glossary_text,
        ""  # No reference examples for this test
    )
    
    print(f"\n✅ Traducción obtenida:")
    print(f"   {result['dutch_translation']}")
    
    # Manual checks
    issues_found = []
    
    # Check formality
    if any(word in result['dutch_translation'].lower() for word in ['je ', ' je', 'jouw', 'jou ']):
        issues_found.append("❌ FALLA: Usa forma informal (je/jouw/jou)")
    else:
        print(f"   ✓ Formalidad: OK (usa 'u/uw')")
    
    # Check Driver•i branding
    if 'driver' in result['dutch_translation'].lower():
        if 'driver•i' in result['dutch_translation'].lower() or 'driver-i' in result['dutch_translation'].lower():
            print(f"   ✓ Branding: OK (mantiene 'Driver•i')")
            
            # Check compound formation
            if 'driver•i app' in result['dutch_translation'].lower() or 'driver-i app' in result['dutch_translation'].lower():
                issues_found.append("❌ FALLA: No forma compuesto con guion (debe ser 'Driver•i-app')")
            elif 'driver•i-app' in result['dutch_translation'].lower() or 'driver-i-app' in result['dutch_translation'].lower():
                print(f"   ✓ Compuesto: OK (usa guion 'Driver•i-app')")
        else:
            issues_found.append("❌ FALLA: No respeta branding 'Driver•i'")
    
    # Check for translationisms
    if 'voor de dag' in result['dutch_translation'].lower():
        issues_found.append("❌ FALLA CRÍTICA: Traduccionismo 'voor de dag' (no existe en holandés)")
    
    if issues_found:
        print(f"\n   🚨 PROBLEMAS DETECTADOS:")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print(f"\n   🎉 ¡Traducción parece correcta!")
    
    results.append({
        "test": test['name'],
        "source": test['source'],
        "translation": result['dutch_translation'],
        "issues": issues_found
    })
    
    time.sleep(2)  # Rate limiting

# Summary
print("\n" + "=" * 80)
print("📊 RESUMEN DE RESULTADOS")
print("=" * 80)

total_tests = len(results)
failed_tests = sum(1 for r in results if r['issues'])
passed_tests = total_tests - failed_tests

print(f"\n✅ Pruebas exitosas: {passed_tests}/{total_tests}")
print(f"❌ Pruebas con problemas: {failed_tests}/{total_tests}")

if failed_tests > 0:
    print(f"\n⚠️  PRUEBAS CON PROBLEMAS:")
    for r in results:
        if r['issues']:
            print(f"\n   {r['test']}:")
            for issue in r['issues']:
                print(f"      {issue}")

print("\n" + "=" * 80)
print("FIN DE PRUEBAS")
print("=" * 80)
