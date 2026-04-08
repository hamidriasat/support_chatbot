import logging
from utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

def load_prompt(file_path: str) -> str:
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Error: Prompt file {file_path} not found.")
        return ""