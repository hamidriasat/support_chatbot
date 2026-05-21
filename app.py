import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pyngrok import ngrok
from models.request_model import InputTextModel
from models.response_model import ResponseModel, VoiceResponseModel
from graph_handler import handle_chat, handle_voice
from utils.config import settings
from integrations.whatsapp import(
    process_text_message,
    process_voice_message, 
    send_whatsapp_text, 
    verify_twilio_signature, 
    cleanup_old_audio_files,
    process_button_reply
)
from paths import PUBLIC_BASE_URL, STATIC_DIR



app = FastAPI(title="Chatbot Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(STATIC_DIR):
    print(f"ERROR: Static directory not found at {STATIC_DIR}")
else:
    print(f"SUCCESS: Static directory found at {STATIC_DIR}")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")



# Endpoint for handling text input
@app.post("/chat", response_model=ResponseModel)
async def chat_endpoint(request: InputTextModel):
    return await handle_chat(
        message=request.message,
        chat_id=request.chat_id
    )


# Endpoint for handling voice input
@app.post("/voice", response_model=VoiceResponseModel)
async def voice_endpoint(
    audio: UploadFile = File(...),
    chat_id: str = Form(...)
):
    return await handle_voice(
        audio=audio,
        chat_id=chat_id
    )


# Endpoint for handling WhatsApp chat
@app.post(
    "/whatsapp",
    response_class=PlainTextResponse,
    status_code=200,
)
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> PlainTextResponse:
    """
    Inbound WhatsApp webhook (Twilio → this server).
 
    Flow:
      1. Parse form body (application/x-www-form-urlencoded).
      2. Verify X-Twilio-Signature — reject fakes with HTTP 403.
      3. Return empty TwiML <Response/> immediately to prevent Twilio retries.
      4. Dispatch text or voice processing as a FastAPI BackgroundTask.
    """
    form_data = dict(await request.form())
 
    # Verify Twilio signature
    path = request.url.path
    query = request.url.query
    full_url = f"{PUBLIC_BASE_URL}{path}" + (f"?{query}" if query else "")
    signature = request.headers.get("X-Twilio-Signature", "")
 
    if not verify_twilio_signature(full_url, form_data, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
 
    # Extract fields
    from_number = form_data.get("From", "")
    chat_id = from_number.replace("whatsapp:", "").strip()
    body = form_data.get("Body", "").strip()
    num_media = int(form_data.get("NumMedia", "0"))
    ButtonPayload: str = Form(None)
    print(f"button payload: {ButtonPayload}\n body: {body}")
 
    # Dispatch
    if num_media > 0:
        media_url: str = form_data.get("MediaUrl0", "")
        media_type: str = form_data.get("MediaContentType0", "")
 
        if media_type.startswith("audio/"):
            background_tasks.add_task(process_voice_message, media_url, chat_id)
            background_tasks.add_task(cleanup_old_audio_files, STATIC_DIR)
        else:
            background_tasks.add_task(
                send_whatsapp_text,
                chat_id,
                "Sorry, I can only process text messages and voice notes."
                " Please send a text or audio message. 🎙️✍️",
            )
    elif ButtonPayload:
        background_tasks.add_task(process_button_reply, ButtonPayload, chat_id)
    else:
        if not body:
            return PlainTextResponse(
                content='<?xml version="1.0" encoding="UTF-8"?><Response/>',
                media_type="text/xml",
            )
        background_tasks.add_task(process_text_message, body, chat_id)
 
    return PlainTextResponse(
        content='<?xml version="1.0" encoding="UTF-8"?><Response/>',
        media_type="text/xml",
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}



if __name__ == "__main__":
    NGROK_TOKEN = settings.get("NGROK_API")
    ngrok.set_auth_token(NGROK_TOKEN)
    clean_domain = PUBLIC_BASE_URL.replace("https://", "").replace("http://", "")
    ngrok_tunnel = ngrok.connect(8000, domain=clean_domain)
    print(f"Ngrok Tunnel Active: {ngrok_tunnel.public_url}")
    print(f"URL Target:  {ngrok_tunnel.public_url}/whatsapp")
    
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=8000)
    finally:
        if ngrok_tunnel:
            print("\nClosing ngrok tunnel...")
            ngrok.disconnect(ngrok_tunnel.public_url)