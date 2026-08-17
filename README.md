# 🏗️ Civil Engineering BIM Extractor

An AI-powered Streamlit web application that helps Civil Engineers extract structured BIM information and measurable dimensions from modern PDF designs or scanned blueprints using Google's Gemini multimodal AI.

This repository contains a lightweight app that accepts PDFs/images, runs batch or single-file extraction, and outputs either strict JSON (for programmatic ingestion) or human-readable Markdown summaries.

## What's new

The app has been improved with several practical features to make batch-processing of drawings reliable and developer-friendly:

- Batch processing UI: upload multiple files and process them in one run. A progress bar and per-file status placeholders show live progress and results.
- Parallel workers: configurable ThreadPoolExecutor workers via a sidebar slider so you can control concurrency for faster throughput.
- Strict JSON and Markdown outputs: choose `Strict JSON` for structured, machine-readable results or `Human-readable Markdown` for inspection and review.
- Robust retries and exponential backoff: API uploads and model calls use a retry helper with exponential backoff to reduce transient failures.
- File upload resilience: files are written to temporary files and uploaded to Gemini with cleanup to avoid leaking temp files.
- Response parsing and recovery: strict JSON parsing is attempted for JSON mode; a safe fallback tries to extract a JSON substring before returning raw text with an error note.
- Downloadable aggregated results: after batch runs you can download a single JSON file containing outputs and a summary for all processed files.
- Secure API key handling: app reads GEMINI_API_KEY from Streamlit secrets or the GEMINI_API_KEY environment variable; an insecure text field is shown only when no key is provided for testing.
- Model initialization and error surfacing: the app initializes the Gemini model lazily and surfaces clear errors when configuration or initialization fails.
- Error reporting per-file: detailed per-file error messages are displayed in the UI so you can quickly identify failed uploads or model calls.

## Quickstart (Run locally)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the Streamlit app:

```bash
streamlit run app.py
```

3. Open the local URL shown in your terminal. Provide your Gemini API key via Streamlit secrets or the `GEMINI_API_KEY` environment variable. If neither is available, you can paste a key into the (insecure) input field for testing.

4. Configure batch settings in the sidebar:
- Output format: `Strict JSON` (for programmatic use) or `Human-readable Markdown` (for review).
- Parallel workers: adjust the number of concurrent workers (1–8).

5. Upload one or more PDF/image files and click "Run batch extraction".

## Output

- JSON mode: produces strict JSON objects per file with keys such as `document_summary`, `key_dimensions`, `structural_elements`, `materials_annotations`, and `confidence_issues`.
- Markdown mode: produces a readable inspection report for each file.
- Aggregated download: a single `bim_batch_results.json` containing all file outputs and a summary is available after the run.

## Notes & Best Practices

- Always verify AI-extracted measurements and structural decisions — AI assists but is not a substitute for professional judgement.
- Prefer providing an API key via Streamlit secrets or an environment variable rather than typing it into the UI.
- If you encounter repeated upload or generation failures, increase the backoff or retry settings in the helper or reduce concurrency.
- For high-volume processing, consider running the app in an environment with a stable network and sufficient concurrency limits.

## Troubleshooting

- "No Gemini API key found": Set `GEMINI_API_KEY` in Streamlit secrets or environment variables.
- "Model not initialized": confirm the API key is valid and you have network access to Gemini endpoints.
- Worker exceptions or frequent transient errors: lower the number of parallel workers or retry the run — the app already retries uploads and model calls.

## License

MIT
