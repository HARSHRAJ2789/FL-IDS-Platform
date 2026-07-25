import os
import socket
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv('FLDS_SERVER_URL', 'http://localhost:8000')
API_KEY = os.getenv('FLDS_API_KEY', '')
INTERFACE = os.getenv('FLDS_INTERFACE', None)  # None = auto-detect
CAPTURE_DURATION = int(os.getenv('FLDS_CAPTURE_DURATION', '300'))  # seconds per capture window
LOCAL_EPOCHS = int(os.getenv('FLDS_LOCAL_EPOCHS', '3'))
BATCH_SIZE = int(os.getenv('FLDS_BATCH_SIZE', '256'))
POLL_INTERVAL = int(os.getenv('FLDS_POLL_INTERVAL', '60'))  # seconds between server polls

DATA_DIR = Path(os.getenv('FLDS_DATA_DIR', './data'))
MODEL_DIR = Path(os.getenv('FLDS_MODEL_DIR', './models'))

HOSTNAME = socket.gethostname()

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
