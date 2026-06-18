from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Job
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook")
async def twilio_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Twilio WhatsApp Webhook
    Expected to receive form data from Twilio (Body, From, To, etc.)
    """
    try:
        form_data = await request.form()
        incoming_msg = form_data.get("Body", "").lower()
        sender_phone = form_data.get("From", "")
        
        logger.info(f"[WhatsApp] Received message from {sender_phone}: {incoming_msg}")
        
        # Determine which job to apply for. For simplicity, grab the first active job.
        job = db.query(Job).filter(Job.is_active == True).first()
        
        if not job:
            reply_text = "We currently have no open positions. Please check back later!"
        else:
            portal_url = f"https://your-talent-portal.com/jobs/{job.id}/apply"
            reply_text = (
                f"Hi! 👋 Thanks for your interest in the {job.title} role at Sarvam AI.\n\n"
                f"To proceed with your application, please click the link below to complete our "
                f"quick AI-powered screening interview:\n\n"
                f"{portal_url}\n\n"
                f"It takes about 10 minutes. Good luck! 🚀"
            )
            
        # Twilio expects a TwiML XML response
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""
        
        from fastapi import Response
        return Response(content=twiml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"[WhatsApp] Webhook error: {e}")
        return {"status": "error"}
