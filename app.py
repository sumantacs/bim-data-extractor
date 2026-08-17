import streamlit as st
import google.generativeai as genai
import os
import tempfile
import json
import time
import concurrent.futures
import traceback
from typing import Any, Dict, Optional
from concurrent.futures import as_completed

# --- App Configuration ---
st.set_page_config(page_title="BIM Data Extractor", page_icon="🏗️", layout="wide")
st.title("🏗️ Civil Engineering BIM Extractor")
st.write("Upload modern PDF designs or scanned blueprints to extract structured BIM information. Use batch mode to process multiple files in parallel.")

# --- API Key Setup (secure) ---
api_key: Optional[str] = None
if st.secrets.get("GEMINI_API_KEY"):
    api_key = st.secrets.get("GEMINI_API_KEY")
elif os.getenv("GEMINI_API_KEY"):
    api_key = os.getenv("GEMINI_API_KEY")
else:
    st.info("No Gemini API key found in Streamlit secrets or the GEMINI_API_KEY environment variable.")
    api_key = st.text_input("Enter your Gemini API Key (insecure, for testing only):", type="password")

if not api_key:
    st.warning("Provide your Gemini API Key via Streamlit secrets or GEMINI_API_KEY env var to proceed.")

# configure client once
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to configure Gemini client: {e}")

# Initialize model once (lazy - only if configured)
MODEL_NAME = 'gemini-1.5-pro-latest'
model = None
if api_key:
    try:
        model = genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        st.error(f"Failed to initialize model {MODEL_NAME}: {e}")

# --- Prompts ---
JSON_PROMPT_TEMPLATE = '''
You are an expert Civil Engineer and BIM specialist.
Analyze the attached design and RETURN ONLY a valid JSON object with the following keys:
- document_summary: string
- key_dimensions: array of objects [{"name": string, "value": number or string, "units": string or null, "location_hint": string or null}]
- structural_elements: array of objects [{"type": string, "location": string or null, "notes": string or null}]
- materials_annotations: array of strings
- confidence_issues: array of strings

If a measurement or item is unclear, use the string "Unclear" or null. DO NOT include extra commentary or markdown — output must be strict JSON.
'''

MARKDOWN_PROMPT_TEMPLATE = '''
You are an expert Civil Engineer and BIM (Building Information Modeling) specialist.
Review the attached design document carefully. Extract the following information and present it in a human-readable Markdown format:

1. Document Summary: What kind of design is this?
2. Key Dimensions: List all detectable lengths, widths, heights, and areas. (Put this in a Markdown table).
3. Structural Elements: Identify walls, columns, beams, doors, and windows.
4. Materials & Annotations: Note any specific materials mentioned or handwritten notes.
5. Confidence/Visibility Issues: Explicitly state if any parts of the document are unreadable, faded, or ambiguous.

Accuracy is critical. If a measurement is unclear, state "Unclear" rather than guessing.
'''

# --- Helper utilities ---

def retry_call(fn, *args, retries=3, backoff=2, **kwargs):
    last_exc = None
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < retries - 1:
                sleep_for = backoff * (2 ** attempt)
                time.sleep(sleep_for)
            else:
                raise


def process_single_file(uploaded_file, prompt_mode: str, model_instance) -> Dict[str, Any]:
    status: Dict[str, Any] = {"filename": uploaded_file.name, "success": False, "output": None, "error": None}
    tmp_path = None
    try:
        # Write to temp file
        suffix = f".{uploaded_file.name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        # Upload file with retries
        try:
            gemini_file = retry_call(genai.upload_file, path=tmp_path, retries=3, backoff=2)
        except Exception as e:
            status["error"] = f"upload_file failed: {str(e)}"
            return status

        # Select prompt
        if prompt_mode == "json":
            prompt = JSON_PROMPT_TEMPLATE
        else:
            prompt = MARKDOWN_PROMPT_TEMPLATE

        # Generate content with retries
        try:
            resp = retry_call(model_instance.generate_content, [gemini_file, prompt], retries=3, backoff=2)
        except Exception as e:
            status["error"] = f"generate_content failed: {str(e)}"
            return status

        text = getattr(resp, "text", str(resp))

        if prompt_mode == "json":
            # Try strict JSON parse
            try:
                parsed = json.loads(text)
                status["output"] = parsed
                status["success"] = True
            except Exception:
                # Attempt to extract JSON substring naive approach
                try:
                    start = text.find('{')
                    end = text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        parsed = json.loads(text[start:end+1])
                        status["output"] = parsed
                        status["success"] = True
                    else:
                        status["output"] = text
                        status["error"] = "response not valid JSON; returned raw text"
                        status["success"] = False
                except Exception:
                    status["output"] = text
                    status["error"] = "failed to parse JSON; returned raw text"
                    status["success"] = False
        else:
            # Markdown mode: return raw text
            status["output"] = text
            status["success"] = True

        return status

    except Exception as e:
        status["error"] = f"Unhandled exception: {traceback.format_exc()}"
        return status

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# --- UI: Batch processing controls ---
st.sidebar.header("Batch settings")
prompt_mode = st.sidebar.radio("Output format:", ("json", "markdown"), index=0, format_func=lambda x: "Strict JSON" if x == "json" else "Human-readable Markdown")
max_workers = st.sidebar.slider("Parallel workers", min_value=1, max_value=8, value=3)

st.sidebar.markdown("Retries and backoff are handled internally (default 3 attempts, exponential backoff).")

uploaded_files = st.file_uploader("Upload blueprints (multiple allowed)", type=['pdf', 'jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files and api_key and model:
    if st.button("Run batch extraction"):
        total = len(uploaded_files)
        progress_bar = st.progress(0)
        # placeholders per file
        file_placeholders = {f.name: st.empty() for f in uploaded_files}
        results = []

        # Run tasks in ThreadPoolExecutor and collect futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {executor.submit(process_single_file, f, prompt_mode, model): f.name for f in uploaded_files}

            completed = 0
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    res = future.result()
                except Exception as e:
                    res = {"filename": name, "success": False, "output": None, "error": f"Worker exception: {e}"}
                results.append(res)

                # update per-file placeholder
                ph = file_placeholders.get(name)
                if res.get("success"):
                    ph.success(f"{name}: processed successfully")
                else:
                    ph.error(f"{name}: failed — {res.get('error')}")

                completed += 1
                progress_bar.progress(int(completed / total * 100))

        # final summary
        success_count = sum(1 for r in results if r.get("success"))
        st.write(f"Batch finished: {success_count}/{total} succeeded")

        # Offer download of aggregated results as JSON
        aggregated = {"files": results, "summary": {"total": total, "succeeded": success_count}}
        st.download_button("Download results (JSON)", data=json.dumps(aggregated, indent=2), file_name="bim_batch_results.json", mime="application/json")

        # For markdown mode optionally show raw outputs inline for inspection
        if prompt_mode == "markdown":
            for r in results:
                st.markdown(f"### {r['filename']}")
                if r.get("output"):
                    st.markdown(r['output'])
                if r.get("error"):
                    st.write(f"Error: {r['error']}")

else:
    if not uploaded_files:
        st.info("Upload one or more PDF/image files to enable batch extraction.")
    elif not api_key:
        st.warning("Provide your Gemini API Key via Streamlit secrets or GEMINI_API_KEY env var to proceed.")
    elif not model:
        st.warning("Model not initialized; check your Gemini configuration and API key.")
