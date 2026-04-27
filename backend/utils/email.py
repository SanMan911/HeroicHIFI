import os
import asyncio
import logging
from config import SENDER_EMAIL

logger = logging.getLogger(__name__)

try:
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
except ImportError:
    resend = None


async def send_otp_email(email: str, otp: str):
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key or not resend:
        logger.info(f"[OTP MOCK] Email: {email}, OTP: {otp}")
        return False
    try:
        resend.api_key = api_key
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "Heroic HIFI Foundation - Email Verification OTP",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
                <h2 style="color:#1E56A0;">Heroic HIFI Foundation</h2>
                <p>Your email verification code is:</p>
                <div style="background:#F0F7FA;padding:20px;text-align:center;border-radius:12px;margin:20px 0;">
                    <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1E56A0;">{otp}</span>
                </div>
                <p style="color:#666;font-size:13px;">This code expires in 10 minutes. If you did not request this, please ignore this email.</p>
            </div>
            """
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Resend email error: {e}")
        return False


async def send_reset_email(email: str, token: str):
    api_key = os.environ.get("RESEND_API_KEY", "")
    frontend_url = os.environ.get("FRONTEND_URL")
    reset_link = f"{frontend_url}/reset-password?token={token}&email={email}"
    if not api_key or not resend:
        logger.info(f"[RESET MOCK] Email: {email}, Token: {token}, Link: {reset_link}")
        return False, reset_link
    try:
        resend.api_key = api_key
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "Heroic HIFI Foundation - Password Reset",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
                <h2 style="color:#1E56A0;">Heroic HIFI Foundation</h2>
                <p>You requested a password reset. Click the link below:</p>
                <div style="margin:20px 0;">
                    <a href="{reset_link}" style="background:#1E56A0;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">Reset Password</a>
                </div>
                <p style="color:#666;font-size:13px;">This link expires in 30 minutes. If you did not request this, please ignore this email.</p>
            </div>
            """
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True, reset_link
    except Exception as e:
        logger.error(f"Reset email error: {e}")
        return False, reset_link


async def send_registration_notification(name: str, email: str, role: str):
    """Send notification to heroic.hifi@proton.me on new registration."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key or not resend:
        return
    try:
        resend.api_key = api_key
        params = {
            "from": SENDER_EMAIL,
            "to": ["heroic.hifi@proton.me"],
            "subject": f"New Registration: {name} ({role})",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
                <h2 style="color:#1E56A0;">New Registration Alert</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Role:</strong> {role}</p>
                <p><strong>Time:</strong> {__import__('datetime').datetime.now().strftime('%d %b %Y, %I:%M %p')}</p>
            </div>
            """
        }
        await asyncio.to_thread(resend.Emails.send, params)
    except Exception as e:
        logger.error(f"Registration notification error: {e}")


async def send_email_blast(subject: str, body: str, recipients: list):
    """Send bulk email blast to list of recipients."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key or not resend:
        logger.info(f"[BLAST MOCK] Subject: {subject}, Recipients: {len(recipients)}")
        return 0
    resend.api_key = api_key
    sent = 0
    for email in recipients:
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [email],
                "subject": subject,
                "html": f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
                    <h2 style="color:#1E56A0;">Heroic HIFI Foundation</h2>
                    <div style="margin:20px 0;line-height:1.6;">{body}</div>
                    <hr style="border:none;border-top:1px solid #E0E0E0;margin:20px 0;">
                    <p style="color:#999;font-size:11px;">You received this because you're a registered member of Heroic HIFI Foundation.</p>
                </div>
                """
            }
            await asyncio.to_thread(resend.Emails.send, params)
            sent += 1
        except Exception as e:
            logger.error(f"Blast email error for {email}: {e}")
    return sent


async def send_notification_email(email: str, subject: str, message: str):
    """Send a notification email to a single user."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key or not resend:
        return False
    try:
        resend.api_key = api_key
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": subject,
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
                <h2 style="color:#1E56A0;">Heroic HIFI Foundation</h2>
                <p>{message}</p>
            </div>
            """
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Notification email error: {e}")
        return False
