import os
from waitress import serve
from app import app  # if your file is app.py; change to: from app_flask_backup import app  if needed

port = int(os.environ.get("PORT", "8000"))
serve(app, host="0.0.0.0", port=port)