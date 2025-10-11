# Asbestos Exposure Educational Estimator (Starter Project)

**Purpose:** a small, rule-based web app (Flask) that estimates cumulative asbestos exposure (f/ml·years) from user-entered roles, with export-to-PDF and clear educational disclaimers. No AI calls enabled yet.

## Quick start (Windows/macOS/Linux)

1. Install Python 3.11+
2. In a terminal:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
3. Open http://127.0.0.1:5000 in your browser.

## Features
- Add one or more roles (task, era, years, frequency, controls).
- Calculate cumulative exposure range and latency.
- Export a nicely formatted PDF summary.
- Placeholder `/ai/parse_history` endpoint for future AI features.

## Packaging as a Windows .exe
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py
dist/app.exe
```
Then double-click `app.exe` to run locally.

## Notes
- Bands are **illustrative**. Replace `BASE_BANDS` with your curated values + references.
- This tool is **educational only** and is **not** medical or legal advice.
- To add AI features later, implement `/ai/parse_history` to map free text → structured roles; keep a clear audit trail of assumptions.

© 2025 Dr [Name] / [Company].
