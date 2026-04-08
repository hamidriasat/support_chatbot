import logging
import os
import warnings


LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

class UTF8StreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # encode/decode to replace unprintable chars instead of crashing
            stream = self.stream
            stream.write(msg + self.terminator)
        except UnicodeEncodeError:
            # replace problematic chars with ?
            msg = self.format(record).encode("utf-8", errors="replace").decode("utf-8")
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()

def setup_logger():
    warnings.filterwarnings("ignore", category=UserWarning)

    console_handler = UTF8StreamHandler()
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("groq").setLevel(logging.WARNING)