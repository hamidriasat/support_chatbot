import base64
import logging
from groq import Groq, APIConnectionError
from utils.config import settings
from utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

GROQ_CLIENT = Groq(api_key=settings.get("GROQ_API_KEY",""))
STT_MODEL = settings.get("STT_MODEL", "whisper-large-v3-turbo")
TTS_MODEL = settings.get("TTS_MODEL", "canopylabs/orpheus-v1-english")


async def sst_groq(audio):
    try:
        audio_bytes = await audio.read()
        transcription = GROQ_CLIENT.audio.transcriptions.create(
            file=(audio.filename, audio_bytes),
            model=STT_MODEL
            )
        return transcription.text.strip()
    except APIConnectionError:
        logger.error("Unable to connect to groq server. Check your GROQ_API_KEY.")
        return "Error: Unable to connect to speech-to-text service."
    except Exception as e:
        error_message = e.body.get('error', {}).get('message', 'Unknown error')
        logger.error(f"Speech-to-text conversion failed: {e}")
        return f"Error: {error_message}"


def tts_groq(text):
    try:
        tts_response = GROQ_CLIENT.audio.speech.create(
            input=text,
            model=TTS_MODEL,
            voice="diana",
            response_format="wav",
            speed=1.0
        )
        audio_bytes = tts_response.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        return audio_base64

    except APIConnectionError:
        logger.error("Unable to connect to groq server. Check your GROQ_API_KEY.")
        return "Error: Unable to connect to text-to-speech service."
    except Exception as e:
        error_message = e.body.get('error', {}).get('message', 'Unknown error')
        logger.error(f"Text-to-speech conversion failed: {e}")
        return f"Error: {error_message}"