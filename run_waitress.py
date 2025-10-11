import os
from waitress import serve
from app import app  # if your main file is app.py; otherwise: from app_flask_backup import app

port = int(os.environ.get("PORT", "8000"))
serve(app, host="0.0.0.0", port=port)