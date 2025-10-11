@'
import os
from waitress import serve
from app import app   # imports `app` from app.py

port = int(os.environ.get("PORT", "8000"))
serve(app, host="0.0.0.0", port=port)
'@ | Set-Content .\run_waitress.py -NoNewline
