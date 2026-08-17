import streamlit as st
import os
import tempfile
import json
import time
import concurrent.futures
import traceback
from typing import Any, Dict, Optional
from concurrent.futures import as_completed

# Optional provider imports (imported inside classes to keep failures local)

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

# Provider selection (pluggable adapter)
PROVIDER_GOOGLE = "google"
PROVIDER_OPENAI = "openai"
provider_choice = st.sidebar.selectbox("AI provider:", (PROVIDER_GOOGLE, PROVIDER_OPENAI), index=0, format_func=lambda x: "Google Gemini" if x == PROVIDER_GOOGLE else "OpenAI (experimental)")

# configure model/provider once (lazy)
MODEL_NAME = 'gemini-1.5-pro-latest'
provider = None

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

# --- JSON Schema for validation ---
try:
    import jsonschema
    from jsonschema import validate
except Exception:
    jsonschema = None

JSON_SCHEMA = {
    "type": "object",
    "required": ["document_summary", "key_dimensions", "structural_elements", "materials_annotations", "confidence_issues"],
    "additionalProperties": False,
    "properties": {
        "document_summary": {"type": "string"},
        "key_dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                    "name": {"type": "string"},
                    "value": {"anyOf": [{"type": "number"}, {"type": "string"}, {"type": "null"}]},
                    "units": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "location_hint": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "additionalProperties": False
            }
        },
        "structural_elements": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string"},
                    "location": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "additionalProperties": False
            }
        },
        "materials_annotations": {"type": "array", "items": {"type": "string"}},
        "confidence_issues": {"type": "array", "items": {"type": "string"}}
    }
}

# --- Provider adapters ---
class ProviderBase:
    def upload_file(self, path: str):
        raise NotImplementedError()

    def generate_content(self, file_ref: Any, prompt: str) -> str:
        raise NotImplementedError()


class GoogleProvider(ProviderBase):
    def __init__(self, api_key: str, model_name: str):
        try:
            import google.generativeai as genai
        except Exception as e:
            raise RuntimeError(f"google-generativeai is not available: {e}")
        self.genai = genai
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            # genai.configure may raise if key invalid; surface later in UI
            pass
        try:
            self.model = genai.GenerativeModel(model_name)
        except Exception:
            # model initialization deferred; model calls will surface errors
            self.model = None

    def upload_file(self, path: str):
        # wrap genai.upload_file with retries handled by caller
        return self.genai.upload_file(path=path)

    def generate_content(self, file_ref: Any, prompt: str) -> str:
        if not self.model:
            # try lazy init
            self.model = self.genai.GenerativeModel(MODEL_NAME)
        resp = self.model.generate_content([file_ref, prompt])
        return getattr(resp, "text", str(resp))


class OpenAIProvider(ProviderBase):
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        # Import heavy OCR dependencies lazily and surface helpful error messages
        try:
            import openai
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image, ImageOps, ImageFilter
        except Exception as e:
            raise RuntimeError(f"OpenAI/OCR dependencies missing: {e}")

        self.openai = openai
        self.openai.api_key = api_key
        self.pytesseract = pytesseract
        self.convert_from_path = convert_from_path
        self.Image = Image
        self.ImageOps = ImageOps
        self.ImageFilter = ImageFilter
        # allow selecting model via env var or param
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def upload_file(self, path: str):
        # The provider uses local path processing (OCR). Return the path as the file reference.
        return path

    def _image_to_text(self, image_path: str) -> str:
        img = self.Image.open(image_path)
        # Basic preprocessing: convert to grayscale, attempt inversion for better contrast, and denoise
        try:
            img = img.convert("L")
            img = self.ImageOps.autocontrast(img)
            img = img.filter(self.ImageFilter.MedianFilter(size=3))
        except Exception:
            pass
        text = self.pytesseract.image_to_string(img)
        return text

    def _pdf_to_text(self, pdf_path: str) -> str:
        pages = self.convert_from_path(pdf_path, dpi=300)
        texts = []
        for page_img in pages:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                page_img.save(tmp.name, format="PNG")
                try:
                    texts.append(self._image_to_text(tmp.name))
                finally:
                    try:
                        os.remove(tmp.name)
                    except Exception:
                        pass
        return "\n\n".join(texts)

    def generate_content(self, file_ref: Any, prompt: str) -> str:
        path = str(file_ref)
        try:
            if path.lower().endswith('.pdf'):
                extracted_text = self._pdf_to_text(path)
            else:
                extracted_text = self._image_to_text(path)
        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {e}")

        # Combine OCR text with the structured prompt. Include clear markers to help the model.
        user_input = (
            "-----BEGIN_EXTRACTED_TEXT-----\n"
            f"{extracted_text}\n"
            "-----END_EXTRACTED_TEXT-----\n\n"
            f"{prompt}"
        )

        try:
            resp = self.openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{"role": "user", "content": user_input}],
                temperature=0.0,
                max_tokens=2000,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")

        # Extract text from response (compatible with multiple shapes)
        try:
            text = resp.choices[0].message.content
        except Exception:
            try:
                text = resp.choices[0].text
            except Exception:
                text = str(resp)

        return text


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


def process_single_file(uploaded_file, prompt_mode: str, provider_instance: ProviderBase) -> Dict[str, Any]:
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
            file_ref = retry_call(provider_instance.upload_file, tmp_path, retries=3, backoff=2)
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
            resp_text = retry_call(provider_instance.generate_content, file_ref, prompt, retries=3, backoff=2)
        except NotImplementedError as nie:
            status["error"] = f"provider not implemented: {str(nie)}"
            return status
        except Exception as e:
            status["error"] = f"generate_content failed: {str(e)}"
            return status

        text = resp_text

        if prompt_mode == "json":
            # Try strict JSON parse
            try:
                parsed = json.loads(text)
                # Validate against schema if jsonschema available
                if jsonschema:
                    try:
                        validate(instance=parsed, schema=JSON_SCHEMA)
                    except Exception as e:
                        status["output"] = parsed
                        status["error"] = f"schema validation failed: {e}"
                        status["success"] = False
                        return status
                status["output"] = parsed
                status["success"] = True
            except Exception:
                # Attempt to extract JSON substring naive approach
                try:
                    start = text.find('{')
                    end = text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        parsed = json.loads(text[start:end+1])
                        if jsonschema:
                            try:
                                validate(instance=parsed, schema=JSON_SCHEMA)
                            except Exception as e:
                                status["output"] = parsed
                                status["error"] = f"schema validation failed after extraction: {e}"
                                status["success"] = False
                                return status
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

# Create provider instance (show user-facing errors if provider not available)
if provider_choice == PROVIDER_GOOGLE:
    try:
        provider = GoogleProvider(api_key, MODEL_NAME) if api_key else None
    except Exception as e:
        provider = None
        st.error(f"Failed to initialize Google provider: {e}")
elif provider_choice == PROVIDER_OPENAI:
    try:
        provider = OpenAIProvider(api_key) if api_key else None
        st.warning("OpenAI provider is experimental — file handling and multimodal requests are not implemented by default.")
    except Exception as e:
        provider = None
        st.error(f"Failed to initialize OpenAI provider: {e}")

uploaded_files = st.file_uploader("Upload blueprints (multiple allowed)", type=['pdf', 'jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files and api_key and provider:
    if st.button("Run batch extraction"):
        total = len(uploaded_files)
        progress_bar = st.progress(0)
        # placeholders per file
        file_placeholders = {f.name: st.empty() for f in uploaded_files}
        results = []

        # Run tasks in ThreadPoolExecutor and collect futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {executor.submit(process_single_file, f, prompt_mode, provider): f.name for f in uploaded_files}

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
    elif not provider:
        st.warning("Provider not initialized; check your provider selection and API key.")
