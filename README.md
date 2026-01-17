# 🇳🇱 AI Technical Translator (English -> Dutch)

A powerful, AI-driven tool for translating technical documents from English to Dutch, ensuring natural phrasing and strict adherence to a glossary.

## Features
- **Strict Glossary Adherence**: Upload your glossary to ensure consistent terminology.
- **Robust AI Backend**: Uses Google Gemini 2.5 Flash for high-quality, context-aware translations.
- **Auto-Correction**: Automatically fixes grammatical errors in the source English before translating.
- **Smart Repair**: Detects and retries failed translations automatically.
- **User-Friendly Interface**: Simple Drag-and-Drop web interface (Streamlit).

## How to Run Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**:
   Double-click `run_translator.bat` OR run:
   ```bash
   python -m streamlit run app.py
   ```

3. **Usage**:
   - Enter your Google API Key (or set `GOOGLE_API_KEY` env var).
   - Upload your `.xlsx` or `.csv` English document.
   - (Optional) Upload your Glossary.
   - Click **Start Translation**.

## Deployment (Streamlit Cloud)

This app is ready for [Streamlit Community Cloud](https://streamlit.io/cloud).

1. Fork this repository.
2. Sign in to Streamlit Cloud.
3. Click **New App** -> Select this repository.
4. In **Advanced Settings**, add your `GOOGLE_API_KEY` as a Secret.
5. Deploy! 🚀
