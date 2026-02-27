import streamlit as st
st.write("Does Streamlit see your key?", "OPENAI_API_KEY" in st.secrets)
import streamlit as st
from openai import OpenAI
import os
from io import BytesIO
from typing import List
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

# Initialize OpenAI client (assumes OPENAI_API_KEY in env / Streamlit secrets)
client = OpenAI

st.set_page_config(page_title="📚 GenAI Study Assistant — Advanced", layout="wide")

# --- Session state init ---
if "summaries_generated" not in st.session_state:
    st.session_state.summaries_generated = 0
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = 0

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    uploaded_file = st.file_uploader("Upload notes (.txt or .pdf)", type=["txt", "pdf"])
    st.markdown("---")
    model = st.selectbox("Model", options=["gpt-4o-mini"], index=0)
    difficulty = st.selectbox("Question difficulty", options=["easy", "medium", "hard"], index=1)
    include_answers = st.checkbox("Include answer keys for questions", value=False)
    st.markdown("---")
    st.markdown("**Progress**")
    st.write(f"Summaries generated: **{st.session_state.summaries_generated}**")
    st.write(f"Question sets generated: **{st.session_state.questions_generated}**")
    st.markdown("---")
    show_examples = st.checkbox("Show sample notes (demo)")
    st.markdown("App built with Streamlit + OpenAI. Keep your API key set in env.")

# --- Utility functions ---
def extract_text_from_pdf(file_bytes: bytes) -> str:
    if PyPDF2 is None:
        return "ERROR: PyPDF2 not installed on server. Please install PyPDF2 to enable PDF uploads."
    text = []
    try:
        reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text.append(page_text)
    except Exception as e:
        return f"ERROR: Could not read PDF: {e}"
    return "\n\n".join(text)

def read_uploaded_file(uploaded) -> str:
    if not uploaded:
        return ""
    if uploaded.type == "application/pdf":
        return extract_text_from_pdf(uploaded.read())
    else:
        try:
            raw = uploaded.read()
            return raw.decode("utf-8", errors="ignore")
        except Exception as e:
            return f"ERROR: Could not read file: {e}"

def call_model_for_summary(notes: str, model_name: str) -> str:
    prompt_system = "You are a helpful assistant that summarizes study notes into concise, well-structured bullet points with short headings."
    user_prompt = f"Summarize these notes into concise bullet points with headings and 6-12 key points:\n\n{notes}"
    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role":"system","content":prompt_system},{"role":"user","content":user_prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content

def call_model_for_questions(notes: str, model_name: str, difficulty: str, include_answers: bool) -> str:
    prompt_system = "You are an exam prep generator. Produce 5 MCQs, 5 short-answer, and 3 long-answer questions based on the notes. Indicate difficulty level next to each question."
    ans_flag = "Include answer keys after each question." if include_answers else "Do not include answer keys; only list questions."
    user_prompt = f"{prompt_system}\nDifficulty: {difficulty}\n{ans_flag}\n\nNotes:\n{notes}"
    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role":"system","content":prompt_system},{"role":"user","content":user_prompt}],
        temperature=0.4,
    )
    return resp.choices[0].message.content

# --- Main UI ---
st.title("📚 GenAI Study Assistant — Advanced")
st.write("Upload `.txt` or `.pdf` notes. Generate summaries, exam-style questions, and quick Q&A.")

col1, col2 = st.columns([3,1])

with col1:
    if show_examples or not uploaded_file:
        with open("sample_notes/example.txt","r", encoding="utf-8") as f:
            sample = f.read()
        st.expander("Sample notes (click to view)", expanded=False).write(sample)
    notes_text = read_uploaded_file(uploaded_file) if uploaded_file else (sample if show_examples else "")
    if notes_text.strip() == "":
        st.info("Upload a `.txt` or `.pdf` file, or toggle 'Show sample notes' in the sidebar.")

    tabs = st.tabs(["📌 Summary", "🔥 Questions", "💬 Q&A"])

    with tabs[0]:
        st.subheader("Summary")
        if st.button("✨ Generate Summary"):
            if not notes_text.strip():
                st.error("No notes available to summarize.")
            else:
                with st.spinner("Generating summary..."):
                    try:
                        summary = call_model_for_summary(notes_text, model)
                        st.session_state.summaries_generated += 1
                        st.success("Summary generated ✅")
                        st.markdown("#### Key Summary")
                        st.info(summary)
                        # Download button
                        st.download_button("📥 Download summary (.txt)", summary, file_name="summary.txt")
                    except Exception as e:
                        st.error(f"Model error: {e}")

    with tabs[1]:
        st.subheader("Generate Exam-style Questions")
        col_a, col_b = st.columns([3,1])
        with col_a:
            st.write("Settings: difficulty set in sidebar. Toggle answer keys in sidebar.")
        with col_b:
            st.write("")
        if st.button("❓ Generate Questions"):
            if not notes_text.strip():
                st.error("No notes available to generate questions.")
            else:
                with st.spinner("Generating questions..."):
                    try:
                        qs = call_model_for_questions(notes_text, model, difficulty, include_answers)
                        st.session_state.questions_generated += 1
                        st.success("Questions generated ✅")
                        st.markdown("#### Questions")
                        st.success(qs)
                        st.download_button("📥 Download questions (.txt)", qs, file_name="questions.txt")
                    except Exception as e:
                        st.error(f"Model error: {e}")

    with tabs[2]:
        st.subheader("Ask a question about your notes")
        user_q = st.text_input("Type a question and press Enter:")
        if user_q:
            if not notes_text.strip():
                st.error("No notes available to answer from.")
            else:
                with st.spinner("Answering..."):
                    try:
                        resp = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role":"system","content":"Answer only using the provided notes. If the information is not present, say so."},
                                {"role":"user","content": f"Notes:\n{notes_text}\n\nQuestion: {user_q}"}
                            ],
                            temperature=0.2,
                        )
                        answer = resp.choices[0].message.content
                        st.markdown("#### Answer")
                        st.info(answer)
                    except Exception as e:
                        st.error(f"Model error: {e}")

with col2:
    st.markdown("### Quick Actions")
    if st.button("Reset progress counters"):
        st.session_state.summaries_generated = 0
        st.session_state.questions_generated = 0
        st.success("Progress reset.")

    st.markdown("---")
    st.markdown("### Notes & Tips")
    st.write("- For large PDFs, extraction may miss scanned pages (images). Use OCR externally for scanned PDFs.")
    st.write("- Keep your API key secure. Set OPENAI_API_KEY in Streamlit Secrets or environment variables.")
