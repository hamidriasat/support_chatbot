import asyncio
import base64
import io
import json
import uuid
import time
from pathlib import Path
import subprocess
import requests
from fastapi import UploadFile
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from graph_handler import handle_chat, handle_voice
from utils.config import settings
from paths import PUBLIC_BASE_URL, STATIC_DIR



TWILIO_ACCOUNT_SID = settings.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = settings.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = settings.get('TWILIO_FROM_NUMBER')
CONTENT_SID = settings.get("TWILIO_CONTENT_SID")
WAITING_NOTE = "\n\n_(Your message is pending approval and will be sent once confirmed. Reply 'yes' or 'no')_"
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def verify_twilio_signature(request_url = None, post_params = None, signature = None):
    '''
    Validates X-Twilio-Signature so we know the request genuinely came from Twilio.
    '''
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    return validator.validate(request_url, post_params, signature)


# ── Twilio send helpers ───────────────────────────────────────────────────────

def send_whatsapp_text(to = None, body = None):
    '''Send a plain-text WhatsApp message via Twilio Messages API.'''
    twilio_client.messages.create(
        from_ = f'''whatsapp:{TWILIO_FROM_NUMBER}''',
        to = f'''whatsapp:{to}''',
        body = body
        )


def send_whatsapp_media(to = None, media_url = None):
    '''
    Send a WhatsApp media message (audio file) via Twilio Messages API.
    `media_url` must be a publicly reachable HTTPS URL — our ngrok static URL.
    Note: Twilio free tier supports sending media on WhatsApp sandbox.
    '''
    twilio_client.messages.create(
        from_ = f'''whatsapp:{TWILIO_FROM_NUMBER}''',
        to = f'''whatsapp:{to}''',
        media_url = [media_url]
        )


def send_whatsapp_interactive(to = None, body = None):
    '''
    Send a WhatsApp interactive message with buttons via Twilio Messages API.
    `buttons` should be a list of dicts.
    '''
    template_vars = {
        "1": body
    }
    twilio_client.messages.create(
        from_ = f'''whatsapp:{TWILIO_FROM_NUMBER}''',
        to = f'''whatsapp:{to}''',
        content_sid= CONTENT_SID,
        content_variables=json.dumps(template_vars)
    )
    print(f"[interactive] Sent buttons to {to}")


def save_audio_and_get_url(audio_base64 = None, chat_id = None):
    '''
    Decodes a base64 audio string → saves it as an OGG file in the static
    directory → returns its publicly accessible ngrok HTTPS URL.
    '''
    audio_dir = Path(STATIC_DIR) / 'audio'
    audio_dir.mkdir(parents = True, exist_ok = True)
    temp_filename = f'''temp_{uuid.uuid4().hex[:8]}'''
    temp_path = audio_dir / temp_filename
    filename = f'''{chat_id.lstrip('+')}_{uuid.uuid4().hex[:8]}.ogg'''
    file_path = audio_dir / filename

    try:
        audio_bytes = base64.b64decode(audio_base64)
        temp_path.write_bytes(audio_bytes)
        subprocess.run([
            'ffmpeg', '-y', '-i', str(temp_path),
            '-c:a', 'libopus', '-b:a', '64k', '-ac', '1',
            str(file_path)
        ], check = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        return f"{PUBLIC_BASE_URL}/static/audio/{filename}"
    except Exception as e:
        print(f"Audio processing error: {e}")
        return ""
    finally:
        if temp_path.exists():
            temp_path.unlink()


async def process_text_message(message = None, chat_id = None):
    '''
    Call chat_endpoint then send the AI response back to the WhatsApp user.
 
    If waiting_for_approval is True, a note is appended so the user knows
    their request is queued for human review.
    '''

    result  = await handle_chat(message=message, chat_id=chat_id) 

    response_text: str = result["response"]
    waiting: bool      = result["waiting_for_approval"]

    if waiting:
        print("sending interactive message: {waiting}")
        send_whatsapp_interactive(
            to=chat_id,
            body=response_text
        )
        return
    
    send_whatsapp_text(to=chat_id, body=response_text)
    print(f"[chat] → {chat_id} | waiting={waiting} | {response_text[:80]!r}")


async def process_voice_message(media_url: str, chat_id: str) -> None:
    

    # Step 1: Download audio from Twilio
    resp = requests.get(
        media_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=30,
    )
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "audio/ogg")
    ext = content_type.split("/")[-1].split(";")[0]
    filename = f"inbound_{chat_id.lstrip('+')}_{uuid.uuid4().hex[:6]}.{ext}"

    # Step 2: Wrap in UploadFile
    upload_file = UploadFile(filename=filename, file=io.BytesIO(resp.content))
    result = await handle_voice(audio=upload_file, chat_id=chat_id)

    transcription = result["transcription"]
    audio_base64 = result["audio"]
    response_text = result["response"]
    is_waiting = result["waiting_for_approval"]

    # Step 3a: Send transcription
    if transcription:
        send_whatsapp_text(
            to=chat_id,
            body=f"🎙️ *Transcription:* {transcription}",
        )
    # check if waiting for approval, if so append note and send interactive message
    if is_waiting:
        send_whatsapp_interactive(
            to=chat_id,
            body=response_text
        )
        return
    
    # Step 3b: Send audio reply
    if audio_base64:
        public_audio_url = save_audio_and_get_url(audio_base64, chat_id)
        send_whatsapp_media(
            to=chat_id,
            media_url=public_audio_url
        )
        await asyncio.sleep(4)
        send_whatsapp_text(
            to=chat_id,
            body=response_text
        )


async def process_button_reply(button_id: str, chat_id: str) -> None:
    """
    Handles the user's button click response.
    Sends the button_id to AI which updates the CSV accordingly.
    """

    if button_id == "yes":
        # Tell AI user confirmed the change
        message="User confirmed the order changes."
        result = await handle_chat(message=message, chat_id=chat_id)
        response_text = result["response"]
        send_whatsapp_text(
            to=chat_id,
            body=f"✅ {response_text}"
        )
        print(f"[button] Order change confirmed by {chat_id}")

    elif button_id == "no":
        # Tell AI user cancelled the change
        message="User cancelled the order change. Please keep the original order.",
        result = await handle_chat(message=message, chat_id=chat_id)
        response_text = result["response"]
        send_whatsapp_text(
            to=chat_id,
            body=f"❌ {response_text}"
        )
        print(f"[button] Order change cancelled by {chat_id}")

    else:
        # Unknown button id — safety net
        print(f"[button] Unknown button_id: {button_id} from {chat_id}")
        send_whatsapp_text(
            to=chat_id,
            body="Sorry, something went wrong. Please try again."
        )


def cleanup_old_audio_files(static_dir = None, max_age_seconds = 120):
    '''
    Scans the static audio directory and deletes files older than `max_age_seconds`.
    '''
    audio_dir = Path(static_dir) / 'audio'
    if not audio_dir.exists():
        return ""
    now = time.time()
    deleted_count = 0
    for file_path in audio_dir.glob('*.ogg'):
        try:
            file_age = now - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"Error deleting file {file_path.name}: {e}")
    if deleted_count > 0:
        print(f'''[Cleanup] Removed {deleted_count} expired audio file(s).''')
