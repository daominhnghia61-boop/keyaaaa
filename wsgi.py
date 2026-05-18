# wsgi.py — entry point for gunicorn (e.g. `gunicorn wsgi:app`)
# Importing app triggers module-level code in app.py, which spawns the
# Telegram bot background thread automatically.
from app import app  # noqa: F401
