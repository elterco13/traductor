import streamlit as st
import pandas as pd
import time
import io
import os
from dotenv import load_dotenv
from backend import TranslatorBackend

load_dotenv()

# Page Config
st.set_page_config(page_title="Translating with Style", layout="wide", page_icon="🇳🇱")

# --- SYNTHWAVE / RETRO DESIGN INJECTION ---
st.markdown("""
<style>
    /* 1. DESIGN TOKENS */
    :root {
      --neon-pink: #ff2e97;
      --electric-blue: #00d2ff;
      --dark-void: #1a0033;
      --sunset-glow: linear-gradient(180deg, #ff8c00 0%, #ff2e97 100%);
      --border-color: #000;
    }

    /* 2. FONTS */
    /* Import fonts for that retro feel */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&family=JetBrains+Mono:wght@400;700&display=swap');

    /* 3. GLOBAL BACKGROUND (THE GRID) */
    .stApp {
      background-color: var(--dark-void);
      /* Use a static grid image or simple gradient as fallback since complex 3D CSS transforms 
         can behave oddly on the main container depending on Streamlit's layout.
         We'll simulate the grid effect on the pseudo-element. */
      font-family: 'JetBrains Mono', monospace;
      color: #fff;
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        width: 200%;
        height: 200%;
        top: -50%;
        left: -50%;
        z-index: -1;
        background-image: 
            linear-gradient(0deg, transparent 24%, rgba(0, 210, 255, .3) 25%, rgba(0, 210, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 210, 255, .3) 75%, rgba(0, 210, 255, .3) 76%, transparent 77%, transparent),
            linear-gradient(90deg, transparent 24%, rgba(0, 210, 255, .3) 25%, rgba(0, 210, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 210, 255, .3) 75%, rgba(0, 210, 255, .3) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
        transform: perspective(500px) rotateX(45deg);
        animation: grid-move 20s linear infinite;
    }

    @keyframes grid-move {
        0% { transform: perspective(500px) rotateX(45deg) translateY(0); }
        100% { transform: perspective(500px) rotateX(45deg) translateY(50px); }
    }

    /* 4. RETRO WINDOWS (CONTAINERS) */
    div[data-testid="stFileUploader"], div[data-testid="stExpander"], div.stTextInput, div.stDataFrame {
        background: rgba(255, 255, 255, 0.9);
        border: 3px solid var(--border-color);
        box-shadow: 8px 8px 0px var(--neon-pink);
        padding: 1rem;
        margin-bottom: 2rem;
        color: black; /* Text inside windows is black */
    }
    
    /* Header simulation for containers */
    div[data-testid="stFileUploader"]::before {
        content: "📂 UPLOAD_SYSTEM_V.1.0";
        display: block;
        background: linear-gradient(90deg, #2d004b, #ff2e97);
        color: white;
        padding: 5px 10px;
        margin: -1rem -1rem 1rem -1rem; /* Negative margins to stretch */
        border-bottom: 3px solid black;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.8rem;
    }

    /* 5. TYPOGRAPHY (TITLES) */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase;
        color: var(--electric-blue) !important;
        text-shadow: 2px 2px 0px var(--neon-pink);
    }
    
    div[data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem;
    }

    /* 6. BUTTONS */
    .stButton > button {
      background: var(--dark-void) !important;
      color: var(--electric-blue) !important;
      border: 2px solid var(--electric-blue) !important;
      font-family: 'Orbitron', sans-serif !important;
      text-transform: uppercase;
      box-shadow: 0 0 10px var(--electric-blue), inset 0 0 5px var(--electric-blue) !important;
      transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
      background: var(--electric-blue) !important;
      color: var(--dark-void) !important;
      box-shadow: 0 0 20px var(--electric-blue) !important;
    }

    /* 7. CRT SCANLINE OVERLAY */
    body::after {
      content: " ";
      display: block;
      position: fixed;
      top: 0; left: 0; bottom: 0; right: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), 
                  linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      z-index: 9999;
      background-size: 100% 2px, 3px 100%;
      pointer-events: none;
    }
    
    /* Sidebar Fix */
    section[data-testid="stSidebar"] {
        background-color: #0b001a;
        border-right: 2px solid var(--electric-blue);
    }
    /* 8. SPECIFIC LABEL COLORS */
    div[data-testid="stTextInput"] label p,
    div[data-testid="stFileUploader"] label p {
        color: var(--neon-pink) !important;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 1rem !important;
        text-shadow: 1px 1px 0px black;
    }

    /* 9. CENTER ALIGNMENT & UPLOADER BUTTONS */
    div.block-container h1, div.block-container h3 {
        text-align: center !important;
    }
    
    /* Browse File button text color */
    [data-testid="stFileUploader"] button {
        color: white !important;
        border-color: white !important;
    }
    [data-testid="stFileUploader"] button:hover {
        border-color: var(--neon-pink) !important;
        color: var(--neon-pink) !important;
    }

</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>⚡Maremi's auto translator ⚡</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Work Smart, not hard, bb. Love U</h3>", unsafe_allow_html=True)



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
        # Reset previous state
        if 'translation_df' in st.session_state:
            del st.session_state['translation_df']
        
        results = []
        errors = []
        total_rows = len(df_source)
        
        # CONTAINER FOR LIVE LOGS
        log_container = st.expander("📜 Process Live Log", expanded=True)
        with log_container:
            st.write("Initializing translation engine...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Placeholder for partial results (so user sees table growing)
        results_placeholder = st.empty()
        
        try:
            # AUTOSAVE INIT
            autosave_file = "TRANSLATION_RESULTS_REALTIME.csv"
            # Initialize/Clear the file with headers
            pd.DataFrame(columns=["original_english", "improved_english", "dutch_translation"]).to_csv(autosave_file, index=False)
            st.info(f"💾 Autosave active. Saving real-time to: `{autosave_file}`")

            for index, row in df_source.iterrows():
                try:
                    text = row[source_col]
                    status_msg = f"Processing row {index+1}/{total_rows}..."
                    status_text.text(status_msg)
                    
                    if index % 10 == 0:
                        with log_container:
                            st.write(f"⏱️ {status_msg}")

                    current_result = None
                    if pd.isna(text) or str(text).strip() == "":
                        # Handle empty
                        current_result = {
                            "original_english": text,
                            "improved_english": "",
                            "dutch_translation": ""
                        }
                    else:
                        # Find terms
                        relevant_terms = backend.find_relevant_terms(str(text), glossary_dict)
                        # Translate
                        current_result = backend.translate_row_robust(str(text), relevant_terms)
                    
                    results.append(current_result)
                    
                    # --- REAL-TIME AUTOSAVE ---
                    # Append this single row to the CSV immediately
                    # We utilize a temporary DF to append safely with quotes/escaping handled by pandas
                    pd.DataFrame([current_result])[["original_english", "improved_english", "dutch_translation"]].to_csv(
                        autosave_file, mode='a', header=False, index=False
                    )
                    # --------------------------
                    
                    # Update Progress
                    progress = (index + 1) / total_rows
                    progress_bar.progress(progress)
                    
                    # VISUAL FEEDBACK: Update table every row so user KNOWS it's working
                    # This might slow it down slightly but provides peace of mind needed right now.
                    if index % 2 == 0 or index == total_rows - 1:
                         results_placeholder.dataframe(pd.DataFrame(results).tail(3))
                         
                except Exception as row_error:
                    err_msg = f"❌ Error on row {index+1}: {str(row_error)}"
                    with log_container:
                        st.error(err_msg)
                    errors.append(err_msg)
                    # Create a dummy failed row so we don't lose alignment
                    failed_row = {
                        "original_english": str(row[source_col]),
                        "improved_english": "ERROR",
                        "dutch_translation": "ERROR_FAILED_PROCESSING"
                    }
                    results.append(failed_row)
                    
                    # Try to autosave the error too so alignment is kept
                    try:
                        pd.DataFrame([failed_row])[["original_english", "improved_english", "dutch_translation"]].to_csv(
                            autosave_file, mode='a', header=False, index=False
                        )
                    except:
                        pass # If saving fails here, we can't do much

            # LOOP FINISHED
            progress_bar.progress(1.0)
            status_text.success(f"✅ Translation Finished! All data saved to {autosave_file}")
            
            # Store Final Results
            st.session_state['translation_df'] = pd.DataFrame(results)
            
            if errors:
                st.warning(f"Process finished with {len(errors)} errors. Check the log above.")
        
        except Exception as e:
            # FATAL CRASH CATCHER
            st.error(f"🔥 FATAL ERROR: The process crashed unexpectedly.\nError details: {e}")
            if results:
                st.warning("⚠️ Attempting to save partial results so you don't lose everything...")
                st.session_state['translation_df'] = pd.DataFrame(results)
            else:
                st.error("No results could be saved.")

    # --- PERSISTENT RESULTS DISPLAY ---
    if 'translation_df' in st.session_state:
        st.divider()
        st.subheader("🎉 Translation Results")
        img_df = st.session_state['translation_df']
        st.dataframe(img_df)
        
        st.write("### Download Options")
        d_col1, d_col2, d_col3 = st.columns(3)

        with d_col1:
            # Download Button CSV (Fixed with BOM for Excel)
            csv = img_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name="translated_results.csv",
                mime="text/csv",
            )

        with d_col2:
            # Download Button Excel (.xlsx)
            output = io.BytesIO()
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    img_df.to_excel(writer, index=False, sheet_name='Translations')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Download Results (Excel)",
                    data=excel_data,
                    file_name="translated_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as e:
                st.error(f"Could not generate Excel file: {e}")

        with d_col3:
            # Download Button XLIFF
            def generate_xliff(df):
                xliff = ['<?xml version="1.0" encoding="UTF-8"?>']
                xliff.append('<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">')
                xliff.append('  <file source-language="en" target-language="nl" datatype="plaintext" original="translation_job">')
                xliff.append('    <body>')
                
                for i, r in df.iterrows():
                    src = str(r.get("original_english", "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    tgt = str(r.get("dutch_translation", "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    
                    xliff.append(f'      <trans-unit id="{i+1}">')
                    xliff.append(f'        <source>{src}</source>')
                    xliff.append(f'        <target>{tgt}</target>')
                    xliff.append('      </trans-unit>')
                
                xliff.append('    </body>')
                xliff.append('  </file>')
                xliff.append('</xliff>')
                return "\n".join(xliff)

            xliff_content = generate_xliff(img_df)
            st.download_button(
                label="📥 Download Results (XLIFF)",
                data=xliff_content,
                file_name="translated_results.xlf",
                mime="application/x-xliff+xml",
            )
