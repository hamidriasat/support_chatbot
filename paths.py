import os
from pathlib import Path
from utils.config import settings
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR: str = os.path.join(BASE_DIR, 'static')
os.makedirs(STATIC_DIR, exist_ok = True)
PUBLIC_BASE_URL: str = settings.get('PUBLIC_BASE_URL')