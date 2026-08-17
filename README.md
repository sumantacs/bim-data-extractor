# 🏗️ Civil Engineering BIM Extractor

An AI-powered Streamlit web application that helps Civil Engineers extract structured BIM information and measurable dimensions from modern PDF designs or scanned blueprints using Google's Gemini model or OpenAI (OCR-backed) provider.

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
- Secure API key handling: app reads GEMINI_API_KEY or OPENAI_API_KEY from Streamlit secrets or the corresponding environment variable; an insecure text field is shown only when no key is provided for testing.
- Model initialization and error surfacing: providers initialize lazily and surface clear errors when configuration or initialization fails.
- Error reporting per-file: detailed per-file error messages are displayed in the UI so you can quickly identify failed uploads or model calls.

## Providers

- Google Gemini (default): Uses `google-generativeai` and the configured MODEL_NAME to upload files and generate content.
- OpenAI (experimental OCR-backed): Uses `pdf2image` + `pytesseract` to extract text from PDFs/images, then sends extracted text to OpenAI's ChatCompletion endpoint. This path is experimental and depends on OCR quality.

## Quickstart (Run locally)

1. Install system dependencies (for OCR/OpenAI provider):

- Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

- macOS (Homebrew):

```bash
brew install tesseract poppler
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Start the Streamlit app:

```bash
streamlit run app.py
```

4. Provide your API keys via Streamlit secrets or environment variables:

- For Google Gemini: GEMINI_API_KEY
- For OpenAI OCR: OPENAI_API_KEY

If neither is available, you can paste a key into the insecure UI field (not recommended for production).

5. Configure batch settings in the sidebar:
- Provider: Google Gemini or OpenAI (experimental)
- Output format: `Strict JSON` (for programmatic use) or `Human-readable Markdown` (for review).
- Parallel workers: adjust the number of concurrent workers (1–8).

6. Upload one or more PDF/image files and click "Run batch extraction".

## Output

- JSON mode: produces strict JSON objects per file with keys such as `document_summary`, `key_dimensions`, `structural_elements`, `materials_annotations`, and `confidence_issues`.
- Markdown mode: produces a readable inspection report for each file.
- Aggregated download: a single `bim_batch_results.json` containing all file outputs and a summary is available after the run.

## Notes & Best Practices

- Always verify AI-extracted measurements and structural decisions — AI assists but is not a substitute for professional judgement.
- Prefer providing API keys via Streamlit secrets or environment variables rather than typing them into the UI.
- If you encounter repeated upload or generation failures, increase the backoff or retry settings in the helper or reduce concurrency.
- For high-volume processing, consider running the app in an environment with a stable network and sufficient concurrency limits.
- OpenAI OCR path depends on the quality of Tesseract OCR. Consider preprocessing scans (deskew, denoise) for better results.

## Troubleshooting

- "No API key found": Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in Streamlit secrets or environment variables.
- "Model not initialized": confirm the API key is valid and you have network access to the provider endpoints.
- Worker exceptions or frequent transient errors: lower the number of parallel workers or retry the run — the app already retries uploads and model calls.

## Developers

- JSON schema validation is available and enforced if `jsonschema` is installed. The schema requires specific keys in the JSON output — see `app.py` for the exact schema.
- To add full multimodal OpenAI uploads (rather than OCR + text prompt), implement an OpenAIProvider variant that uploads files and calls a vision-enabled endpoint.

## License

MIT
