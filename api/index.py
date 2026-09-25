import sys
import os

# Add root project directory to sys.path so all imports (flask_app, src, config) resolve cleanly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask_app import app

# Vercel serverless WSGI entrypoint
if __name__ == "__main__":
    app.run()
