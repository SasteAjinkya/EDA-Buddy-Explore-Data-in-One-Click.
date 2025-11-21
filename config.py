import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_CONTENT_LENGTH = 16 * 1024 * 1024
SECRET_KEY = os.environ.get('FLASK_SECRET', 'change-this-secret-in-prod')
