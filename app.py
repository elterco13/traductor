import streamlit as st
import pandas as pd
import time
import os
from dotenv import load_dotenv
from backend import TranslatorBackend

load_dotenv()

# Page Config
st.set_page_config(page_title="Translating with Style", layout="wide", page_icon="🇳🇱")

# --- MEMPHIS DESIGN INJECTION ---
st.markdown("""
<style>
    /* VARIABLES */
    :root {
      --m-yellow: #ffee10;
      --m-pink: #ff6ad5;
      --m-teal: #87e1ff;
      --m-purple: #ad8cff;
      --m-black: #000000;
      --m-white: #ffffff;
      --border-width: 4px;
    }

    /* GLOBAL BACKGROUND */
    .stApp {
      background-color: #f0f0f0;
      background-image: radial-gradient(var(--m-black) 10%, transparent 10%);
      background-size: 30px 30px;
      font-family: 'Arial Black', sans-serif;
    }

    /* CARD-LIKE CONTAINERS FOR STREAMLIT WIDGETS */
    div[data-testid="stFileUploader"], div[data-testid="stExpander"], div.stTextInput {
        background: var(--m-white);
        border: var(--border-width) solid var(--m-black) !important;
        box-shadow: 10px 10px 0px var(--m-purple);
        padding: 1rem;
        margin-bottom: 2rem;
        transform: rotate(-1deg);
        transition: transform 0.2s;
    }
    
    div[data-testid="stFileUploader"]:hover {
        transform: rotate(0deg) scale(1.02);
    }

    /* HEADERS */
    h1, h2, h3 {
        color: var(--m-black) !important;
        text-transform: uppercase;
        text-shadow: 4px 4px 0px var(--m-yellow);
        font-weight: 900 !important;
    }

    /* BUTTONS */
    .stButton > button {
      background-color: var(--m-teal) !important;
      color: var(--m-black) !important;
      border: var(--border-width) solid var(--m-black) !important;
      font-weight: 900 !important;
      text-transform: uppercase;
      box-shadow: 5px 5px 0px var(--m-black) !important;
      transition: all 0.1s ease !important;
      padding: 0.5rem 2rem !important;
      font-size: 1.2rem !important;
    }

    .stButton > button:hover {
      transform: translate(-2px, -2px);
      box-shadow: 7px 7px 0px var(--m-black) !important;
      background-color: var(--m-pink) !important;
    }

    .stButton > button:active {
      transform: translate(2px, 2px);
      box-shadow: 0px 0px 0px var(--m-black) !important;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: var(--m-yellow);
        border-right: var(--border-width) solid var(--m-black);
    }

    /* SHAPES (DECORATIVE) */
    .shape {
      position: fixed;
      border: var(--border-width) solid var(--m-black);
      z-index: 0;
      pointer-events: none;
    }
    .circle-deco {
      width: 100px;
      height: 100px;
      background: var(--m-pink);
      border-radius: 50%;
      top: 10%;
      right: 5%;
      animation: float 6s infinite alternate;
    }
    .triangle-deco {
      width: 0;
      height: 0;
      border-left: 50px solid transparent;
      border-right: 50px solid transparent;
      border-bottom: 90px solid var(--m-teal);
      top: 80%;
      left: 5%;
      transform: rotate(15deg);
      position: fixed;
      z-index: 0;
    }
    @keyframes float {
      from { transform: translateY(0); }
      to { transform: translateY(-20px); }
    }
</style>

<!-- DECORATIVE SHAPES -->
<div class="shape circle-deco"></div>
<div class="triangle-deco"></div>
""", unsafe_allow_html=True)

st.title("⚡ PROYECTO MEMPHIS: TRANSLATOR")
st.markdown("**Explorando el caos visual con geometría y color.**")



# Sidebar Configuration
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Google API Key", type="password", help="Enter your Gemini API Key")

# Use environment variable or Streamlit secrets if available
if not api_key_input:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key_input = st.secrets["GOOGLE_API_KEY"]
    elif "GOOGLE_API_KEY" in os.environ:
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
