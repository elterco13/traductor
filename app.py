import streamlit as st
import pandas as pd
import time
import os
from backend import TranslatorBackend

# Page Config
st.set_page_config(page_title="AI Translator (EN -> NL)", layout="wide")

st.title("🇳🇱 Technical Translator AI (EN -> NL)")
st.markdown("Upload your English document and Glossary to translate automatically.")

# Sidebar Configuration
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Google API Key", type="password", help="Enter your Gemini API Key")

# Use environment variable if available as default
if not api_key_input and "GOOGLE_API_KEY" in os.environ:
    api_key_input = os.environ["GOOGLE_API_KEY"]

if not api_key_input:
    st.warning("⚠️ Please provide an API Key to proceed.")
    st.stop()

# Initialize Backend
backend = TranslatorBackend(api_key_input)

# File Uploads
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Source Document")
    source_file = st.file_uploader("Upload .csv or .xlsx (English)", type=["csv", "xlsx"])

with col2:
    st.subheader("2. Glossary (Optional)")
    glossary_file = st.file_uploader("Upload Glossary .csv or .xlsx (Term | Translation)", type=["csv", "xlsx"])

# Data Preview & Logic
if source_file:
    try:
        if source_file.name.endswith('.csv'):
            df_source = pd.read_csv(source_file)
        else:
            df_source = pd.read_excel(source_file)
        
        st.write("Preview of Source File:")
        st.dataframe(df_source.head(3))
        
        # Select Source Column
        # Auto-detect 'source' or 'en_us'
        default_col_idx = 0
        for i, col in enumerate(df_source.columns):
            if 'source' in col.lower() or 'en_us' in col.lower():
                default_col_idx = i
                break
        
        source_col = st.selectbox("Select Column with English Text", df_source.columns, index=default_col_idx)

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # Glossary Processing
    glossary_dict = {}
    if glossary_file:
        try:
            if glossary_file.name.endswith('.csv'):
                df_gloss = pd.read_csv(glossary_file)
            else:
                df_gloss = pd.read_excel(glossary_file)
            
            glossary_dict = backend.build_glossary_dict(df_gloss)
            st.success(f"✅ Glossary loaded: {len(glossary_dict)} terms")
        except Exception as e:
            st.error(f"Error reading glossary: {e}")

    # Process Button
    if st.button("🚀 Start Translation", type="primary"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_rows = len(df_source)
        
        # Create a placeholder for the dataframe results
        results_placeholder = st.empty()
        
        for index, row in df_source.iterrows():
            text = row[source_col]
            
            # Update Status
            status_text.text(f"Processing row {index+1}/{total_rows}...")
            
            if pd.isna(text) or str(text).strip() == "":
                # Handle empty
                results.append({
                    "original_english": text,
                    "improved_english": "",
                    "dutch_translation": ""
                })
            else:
                # Find terms
                relevant_terms = backend.find_relevant_terms(str(text), glossary_dict)
                
                # Translate
                # We can hardcode reference examples or make it dynamic later. 
                # For now, simplistic dynamic set is fine or empty.
                translation = backend.translate_row_robust(str(text), relevant_terms)
                results.append(translation)
            
            # Update Progress
            progress = (index + 1) / total_rows
            progress_bar.progress(progress)
            
            # Show mid-process results in a small table every 5 rows
            if index % 5 == 0:
                current_df = pd.DataFrame(results)
                results_placeholder.dataframe(current_df.tail(3))
        
        # Finalization
        progress_bar.progress(1.0)
        status_text.text("✅ Translation Complete!")
        
        img_df = pd.DataFrame(results)
        results_placeholder.dataframe(img_df)
        
        # Download Button
        csv = img_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name="translated_results.csv",
            mime="text/csv",
        )
