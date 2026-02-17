"""
SwasthyaSahayak — WhatsApp Business API Webhook (Twilio).

Handles incoming WhatsApp messages (text + voice notes) and routes them
through the SwasthyaSahayak triage conversation engine.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SETUP GUIDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install dependencies:
     pip install twilio openai-whisper

2. Set environment variables (create a .env file or export):
     TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     TWILIO_AUTH_TOKEN=your_auth_token_here
     TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

3. Start the webhook server:
     uvicorn app.whatsapp_webhook:app --host 0.0.0.0 --port 8001

4. Expose locally for testing with ngrok:
     ngrok http 8001
     → Copy the HTTPS URL (e.g. https://abc123.ngrok.io)

5. In Twilio Console → Messaging → WhatsApp Sandbox:
     When a message comes in: https://abc123.ngrok.io/whatsapp/incoming
     Method: POST

6. Send "join <sandbox-keyword>" to the Twilio sandbox number on WhatsApp,
   then send your first message to start triage.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENDPOINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  POST /whatsapp/incoming  — Twilio webhook (text + voice)
  GET  /whatsapp/health    — Health check
"""

import os
import logging
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import PlainTextResponse

from channels.whatsapp_handler import process_message
from channels.voice_handler import transcribe_url
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Twilio Configuration ──────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

_twilio_client   = None
_twilio_validator = None


def _get_twilio_client():
    """Lazy-init Twilio REST client."""
    global _twilio_client
    if _twilio_client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise RuntimeError(
                "Twilio credentials not configured. "
                "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables."
            )
        from twilio.rest import Client
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


def _get_validator():
    """Lazy-init Twilio RequestValidator for signature verification."""
    global _twilio_validator
    if _twilio_validator is None and TWILIO_AUTH_TOKEN:
        from twilio.request_validator import RequestValidator
        _twilio_validator = RequestValidator(TWILIO_AUTH_TOKEN)
    return _twilio_validator


def _validate_twilio_request(request: Request, form_data: dict) -> bool:
    """
    Validate that the incoming request genuinely originated from Twilio
    by checking the X-Twilio-Signature header.

    Returns True in development mode (no credentials configured).
    Always validates in production (credentials set).
    """
    validator = _get_validator()
    if validator is None:
        logger.warning("Twilio validator not configured — skipping signature check (dev mode).")
        return True

    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    is_valid = validator.validate(url, form_data, signature)
    if not is_valid:
        logger.warning(f"Invalid Twilio signature for request from {request.client.host}")
    return is_valid


def _send_whatsapp_reply(to: str, body: str) -> None:
    """Send a WhatsApp message to the user via Twilio."""
    try:
        client = _get_twilio_client()
        msg = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=to,
            body=body,
        )
        logger.info(f"WhatsApp reply sent | SID={msg.sid} | to={to[:20]}...")
    except RuntimeError as e:
        logger.error(f"Twilio not configured: {e}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp reply to {to[:20]}: {e}")


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="SwasthyaSahayak — WhatsApp Webhook",
    version="2.0",
    description="WhatsApp channel for AI medical triage via Twilio",
)


@app.get("/whatsapp/health")
def health_check():
    """Health check endpoint."""
    return {
        "status":             "healthy",
        "version":            "2.0",
        "twilio_configured":  bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        "whatsapp_from":      TWILIO_WHATSAPP_FROM if TWILIO_ACCOUNT_SID else "not_configured",
    }


@app.post("/whatsapp/incoming")
async def whatsapp_incoming(
    request:             Request,
    From:                str = Form(...),
    Body:                str = Form(default=""),
    NumMedia:            int = Form(default=0),
    MediaUrl0:           str = Form(default=None),
    MediaContentType0:   str = Form(default=None),
):
    """
    Twilio WhatsApp webhook endpoint.

    Handles:
      - Text messages → conversation state machine
      - Voice notes   → Whisper STT → conversation state machine
      - Images/other  → polite rejection message

    Twilio sends POST with application/x-www-form-urlencoded.
    """
    # Collect raw form data for signature validation
    form_data = dict(await request.form())

    if not _validate_twilio_request(request, form_data):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature.")

    phone_number  = From   # e.g. "whatsapp:+919876543210"
    message_text  = Body.strip()
    content_type  = (MediaContentType0 or "").lower()

    logger.info(
        f"Incoming WhatsApp | from={phone_number[:20]}... | "
        f"NumMedia={NumMedia} | body_len={len(message_text)}"
    )

    # ── Voice Note ────────────────────────────────────────────────────────────
    if NumMedia and NumMedia > 0 and MediaUrl0 and "audio" in content_type:
        logger.info(f"Voice note received ({content_type}). Starting transcription...")
        try:
            transcription = transcribe_url(
                audio_url=MediaUrl0,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None,
            )
            message_text = transcription["text"]
            lang_name    = transcription["language_name"]
            duration_s   = transcription.get("duration_s", 0)

            logger.info(f"Transcribed ({lang_name}, {duration_s:.1f}s): '{message_text[:100]}'")

            # Prepend transcription confirmation so user knows their voice was understood
            voice_prefix = (
                f"🎤 *Voice note received ({lang_name}, {duration_s:.0f}s)*\n"
                f'_I heard: "{message_text[:100]}{"..." if len(message_text) > 100 else ""}"_\n\n'
            )
        except RuntimeError as e:
            # Whisper not installed
            _send_whatsapp_reply(
                phone_number,
                "⚠️ Voice transcription is not available on this server.\n"
                "Please *type* your symptoms as a text message instead.",
            )
            return PlainTextResponse("ok")
        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            _send_whatsapp_reply(
                phone_number,
                "Sorry, I could not process your voice note.\n"
                "Please type your symptoms as text, or send the voice note again.",
            )
            return PlainTextResponse("ok")

    # ── Non-audio media (image, document, video) ──────────────────────────────
    elif NumMedia and NumMedia > 0 and MediaUrl0 and "audio" not in content_type:
        _send_whatsapp_reply(
            phone_number,
            "📎 I received a media file, but I can only process *text messages* and *voice notes*.\n"
            "Please describe your symptoms in text or send a voice note.",
        )
        return PlainTextResponse("ok")

    # ── No message body ───────────────────────────────────────────────────────
    if not message_text:
        _send_whatsapp_reply(
            phone_number,
            "Please send your symptoms as a text or voice message.\n"
            "_Type *hi* to start._",
        )
        return PlainTextResponse("ok")

    # ── Route through conversation engine ─────────────────────────────────────
    reply = process_message(phone_number, message_text)

    # Prepend voice transcription note if applicable
    if NumMedia and NumMedia > 0 and MediaUrl0 and "audio" in content_type:
        reply = voice_prefix + reply

    _send_whatsapp_reply(phone_number, reply)
    return PlainTextResponse("ok")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
