
# 📚 GenAI Study Assistant — Advanced

Enhanced Streamlit app with:
- PDF and TXT upload support
- Difficulty selector for question generation (easy/medium/hard)
- Option to include answer keys
- Simple progress tracker (counts summaries and question sets generated)
- Downloadable summary and question text files

## Quickstart
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Set your OpenAI API key in environment:
```bash
export OPENAI_API_KEY="your_api_key_here"
# or set in Streamlit Secrets on Streamlit Cloud
```
3. Run the app:
```bash
streamlit run app.py
```

## Notes
- PDF extraction uses `PyPDF2`. For scanned PDFs you will need OCR (not included).
- Model used: `gpt-4o-mini` (change in app if needed).
