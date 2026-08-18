# 🏗️ Civil Engineering BIM Extractor

An AI-powered Streamlit web application that helps Civil Engineers extract structured BIM information and measurable dimensions from modern PDF designs or scanned blueprints using Google's Gemini model.

This repository contains a lightweight app that accepts PDFs/images, runs batch or single-file extraction, and outputs either strict JSON (for programmatic ingestion) or human-readable Markdown summaries.

## What's new

The app has been improved with several practical features to make batch-processing of drawings reliable and developer-friendly:

- Batch processing UI: upload multiple files and process them in one run. A progress bar and per-file status placeholders show live progress and results.
- Parallel workers: configurable ThreadPoolExecutor workers via a sidebar slider so you can control concurrency for faster throughput.
- Strict JSON and Markdown outputs: choose `Strict JSON` for structured, machine-readable results or `Human-readable Markdown` for inspection and review.
- Robust retries and exponential backoff: API uploads and model calls use a retry helper with exponential backoff to reduce transient failures.
- File upload resilience: files are written to temporary files and uploaded to Gemini (or processed by the OpenAI OCR adapter) with cleanup to avoid leaking temp files.
- Response parsing and recovery: strict JSON parsing is attempted for JSON mode; a safe fallback tries to extract a JSON substring before returning raw text with an error note.
- Downloadable aggregated results: after batch runs you can download a single JSON file containing outputs and a summary for all processed files.
- Secure API key handling: app reads GEMINI_API_KEY or OPENAI_API_KEY from Streamlit secrets or the corresponding environment variable; an insecure text field is shown only when no key is provided.
- Model initialization and error surfacing: providers initialize lazily and surface clear errors when configuration or initialization fails.
- Error reporting per-file: detailed per-file error messages are displayed in the UI so you can quickly identify failed uploads or model calls.

## Providers

- Google Gemini (default): Uses `google-generativeai` and the configured MODEL_NAME to upload files and generate content.
- OpenAI (experimental OCR-backed): Uses `pdf2image` + `pytesseract` to extract text from PDFs/images, then sends extracted text to OpenAI's ChatCompletion endpoint. This path is experimental and requires Tesseract OCR and Poppler tools.

## Installation Guide

### Windows Installation (Recommended for Most Users)

Follow these steps to set up the BIM Data Extractor on Windows:

#### Step 1: Install Python
1. Download Python 3.9+ from [python.org](https://www.python.org/downloads/)
2. **Important**: During installation, check ☑️ "Add Python to PATH"
3. Click "Install Now" or customize as needed
4. Verify installation by opening Command Prompt and running:
   ```bash
   python --version
   pip --version
   ```

#### Step 2: Download This Repository
Option A - Using Git (if installed):
```bash
git clone https://github.com/sumantacs/bim-data-extractor.git
cd bim-data-extractor
```

Option B - Download as ZIP:
1. Visit [https://github.com/sumantacs/bim-data-extractor](https://github.com/sumantacs/bim-data-extractor)
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Open Command Prompt and navigate to the extracted folder:
   ```bash
   cd C:\path\to\bim-data-extractor
   ```

#### Step 3: Create a Python Virtual Environment (Recommended)
Creating a virtual environment keeps dependencies isolated:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

You should see `(venv)` appear in your Command Prompt. To deactivate later, simply type `deactivate`.

#### Step 4: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Install System Dependencies (Optional - Only for OpenAI OCR Provider)

**If you only plan to use Google Gemini, skip this step.**

For OpenAI provider, you need Tesseract OCR and Poppler utilities:

**Option A - Using Chocolatey (Easy - Recommended)**
1. Open Command Prompt **as Administrator**
2. Install Chocolatey if you don't have it: Copy-paste this command:
   ```bash
   @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
   ```
3. Close and reopen Command Prompt as Administrator
4. Install Tesseract and Poppler:
   ```bash
   choco install tesseract-ocr poppler
   ```

**Option B - Manual Installation**

*Tesseract OCR:*
1. Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (default installation is fine)
3. Add to your Python environment variable in your app initialization

*Poppler:*
1. Download from [Poppler releases](https://github.com/oschwartz10612/poppler-windows/releases)
2. Extract to a folder (e.g., `C:\poppler`)
3. Add to PATH or specify in your code

#### Step 6: Get API Keys

**For Google Gemini (Recommended):**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Click "Create API Key"
3. Copy your API key

**For OpenAI (Optional):**
1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Copy your API key

#### Step 7: Set Up API Keys

**Option A - Environment Variables (Recommended for Security)**

1. Open Command Prompt
2. Set environment variable temporarily (for current session):
   ```bash
   set GEMINI_API_KEY=your_actual_api_key_here
   ```
   Or for OpenAI:
   ```bash
   set OPENAI_API_KEY=your_actual_api_key_here
   ```

To make it permanent (survives restarts):
1. Press `Win + X` → "System"
2. Click "Advanced system settings" → "Environment Variables"
3. Click "New" under "User variables"
4. Variable name: `GEMINI_API_KEY` (or `OPENAI_API_KEY`)
5. Variable value: paste your API key
6. Click "OK" and restart Command Prompt

**Option B - Streamlit Secrets (For Development)**

1. Create folder: `.streamlit` (with a dot at the beginning)
2. Inside, create file `secrets.toml`
3. Add your keys:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   OPENAI_API_KEY = "your_optional_openai_key_here"
   ```

#### Step 8: Run the Application

Make sure your virtual environment is activated (you should see `(venv)` in your prompt):

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### macOS Installation

1. Install system dependencies using Homebrew:

```bash
brew install tesseract poppler python@3.11
```

2. Install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Set API keys:

```bash
export GEMINI_API_KEY="your_key_here"
# or
export OPENAI_API_KEY="your_key_here"
```

4. Run the app:

```bash
streamlit run app.py
```

### Linux/Debian/Ubuntu Installation

1. Install system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv tesseract-ocr poppler-utils
```

2. Install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Set API keys:

```bash
export GEMINI_API_KEY="your_key_here"
# or
export OPENAI_API_KEY="your_key_here"
```

4. Run the app:

```bash
streamlit run app.py
```

## Quickstart (After Installation)

1. Ensure your virtual environment is activated
2. Run: `streamlit run app.py`
3. The app opens at `http://localhost:8501`
4. Configure provider and settings in the sidebar:
   - Provider: Google Gemini (recommended) or OpenAI (experimental)
   - Output format: `Strict JSON` or `Human-readable Markdown`
   - Parallel workers: 1-8 (adjust based on your system)
5. Upload PDF/image files
6. Click "Run batch extraction"
7. Download results as JSON when complete

## Output

- JSON mode: produces strict JSON objects per file with keys such as `document_summary`, `key_dimensions`, `structural_elements`, `materials_annotations`, and `confidence_issues`.
- Markdown mode: produces a readable inspection report for each file.
- Aggregated download: a single `bim_batch_results.json` containing all file outputs and a summary is available after the run.

## Notes & Best Practices

- Always verify AI-extracted measurements and structural decisions — AI assists but is not a substitute for professional judgement.
- Prefer providing API keys via environment variables or Streamlit secrets rather than typing them into the UI.
- If you encounter repeated upload or generation failures, increase the backoff or retry settings in the helper or reduce concurrency.
- For high-volume processing, consider running the app in an environment with a stable network and sufficient concurrency limits.
- OpenAI OCR path depends on the quality of Tesseract OCR. Consider preprocessing scans (deskew, denoise) for better results.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No API key found" | Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in environment variables or `.streamlit/secrets.toml` |
| "Python is not recognized" | Ensure Python is added to PATH. Reinstall Python and check "Add Python to PATH" |
| "ModuleNotFoundError" | Activate your virtual environment: `venv\Scripts\activate` |
| "Model not initialized" | Verify API key is valid and you have internet connection |
| Tesseract not found (Windows) | Reinstall Tesseract and ensure it's in PATH, or add path manually in code |
| Worker exceptions | Lower the number of parallel workers or retry the run |
| Port 8501 already in use | Run on different port: `streamlit run app.py --server.port 8502` |

## Developers

- JSON schema validation is available and enforced if `jsonschema` is installed. The schema requires specific keys in the JSON output — see `app.py` for the exact schema.
- To add full multimodal OpenAI uploads (rather than OCR + text prompt), implement an OpenAIProvider variant that uploads files and calls a vision-enabled endpoint.

## License

MIT
