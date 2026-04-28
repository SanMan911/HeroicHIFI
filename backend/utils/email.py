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


async def send_query_response_email(query: dict, response_text: str, admin: dict) -> bool:
    """Email a reply back to the visitor who submitted a Contact Us query."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key or not resend:
        return False
    try:
        resend.api_key = api_key
        admin_name = admin.get("name") or admin.get("email", "Heroic HIFI Foundation")
        # Preserve the visitor's original message in the reply for context
        original = (query.get("message") or "").replace("<", "&lt;").replace(">", "&gt;")
        reply_html = response_text.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        params = {
            "from": SENDER_EMAIL,
            "to": [query["email"]],
            "subject": f"Re: {query.get('subject', 'Your enquiry')} — Heroic HIFI Foundation",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;background:#f8fafc;">
              <div style="background:white;border-radius:12px;padding:24px;border:1px solid #e0e7ff;">
                <h2 style="color:#1E56A0;margin:0 0 4px 0;">Heroic HIFI Foundation</h2>
                <p style="color:#94a3b8;font-size:12px;margin:0 0 24px 0;">A Section 8 Non-Profit Organisation</p>
                <p style="color:#0D2847;">Hello {query.get('name', 'there')},</p>
                <p style="color:#475569;line-height:1.6;">Thank you for reaching out to us. Please find our response below:</p>
                <div style="background:#f1f5f9;border-left:4px solid #1E56A0;padding:14px 16px;margin:18px 0;border-radius:6px;color:#0D2847;line-height:1.7;">
                  {reply_html}
                </div>
                <p style="color:#475569;line-height:1.6;">If you have follow-up questions, simply reply to this email or visit our Contact page.</p>
                <p style="color:#0D2847;margin:24px 0 4px 0;font-weight:600;">Warm regards,</p>
                <p style="color:#0D2847;margin:0;">{admin_name}<br/><span style="color:#94a3b8;font-size:12px;">Heroic HIFI Foundation</span></p>
                <hr style="margin:24px 0;border:none;border-top:1px solid #e2e8f0;">
                <p style="color:#94a3b8;font-size:11px;margin:0;">Your original message:</p>
                <blockquote style="color:#94a3b8;font-size:12px;margin:6px 0 0 0;padding-left:12px;border-left:2px solid #e2e8f0;font-style:italic;">{original}</blockquote>
              </div>
            </div>
            """,
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Query response email error: {e}")
        return False



async def send_donation_receipt_email(donation: dict, pdf_bytes: bytes, label: str = "donation") -> bool:
    """Email the donor a PROVISIONAL receipt (not a tax certificate).
    The consolidated 80G certificate is sent separately on 1 April for the prior FY.

    `label` distinguishes flow type in the subject line ("recurring", "donation", "replayed").
    Returns True if Resend accepted the message, False otherwise (logged and swallowed).
    """
    import base64
    from datetime import date
    from routes.certificates import fy_for_date
    api_key = os.environ.get("RESEND_API_KEY", "")
    email = (donation.get("email") or "").strip().lower()
    if not api_key or not resend or not email:
        logger.info(f"[RECEIPT MOCK] would email {email} with provisional receipt PDF ({len(pdf_bytes)} bytes)")
        return False
    try:
        resend.api_key = api_key
        amount = donation.get("amount", 0)
        donation_id = donation.get("id", "")
        donor_name = donation.get("name", "")
        when_str = donation.get("created_at", "")[:10] or date.today().isoformat()
        try:
            d = date.fromisoformat(when_str)
        except Exception:
            d = date.today()
        fy_start, fy_end, fy_label = fy_for_date(d)
        cert_send_date = date(fy_end.year, 4, 1).strftime("%d %B %Y")
        subject = (
            f"Donation Acknowledgment — ₹{amount:,} (Provisional Receipt)"
            if label == "donation"
            else f"Recurring Donation Acknowledgment — ₹{amount:,} (Provisional Receipt, {label})"
        )
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": subject,
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:580px;margin:0 auto;padding:20px;">
                <h2 style="color:#1E56A0;margin:0 0 4px;">Heroic HIFI Foundation</h2>
                <p style="color:#666;font-size:12px;margin:0 0 18px;">Section 8 Non-Profit Organization, India</p>
                <p style="font-size:14px;line-height:1.6;">
                    Dear {donor_name or 'Donor'},<br/><br/>
                    Thank you for your generous contribution of <strong>₹{amount:,}</strong>{f' ({label})' if label != 'donation' else ''} on {when_str}.
                    A provisional receipt is attached to this email for your records.
                </p>
                <div style="background:#FEF2F2;border:1.5px solid #FCA5A5;border-radius:12px;padding:14px;margin:18px 0;">
                    <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:#B91C1C;letter-spacing:0.05em;">
                        ⚠ THIS IS NOT AN 80G TAX CERTIFICATE
                    </p>
                    <p style="margin:0;font-size:13px;color:#0D2847;line-height:1.55;">
                        The attached provisional receipt <strong>cannot be used to claim a tax deduction</strong>.
                        Your <strong>consolidated 80G certificate</strong> covering all donations made
                        during <strong>FY {fy_label}</strong> (1 April {fy_start.year} – 31 March {fy_end.year})
                        will be auto-emailed to you on or shortly after <strong>{cert_send_date}</strong>.
                        Please use that document — and not this receipt — for your income tax filing.
                    </p>
                </div>
                <p style="font-size:12px;color:#94a3b8;margin-top:24px;">
                    With heartfelt gratitude,<br/>The Heroic HIFI Team
                </p>
            </div>
            """,
            "attachments": [{
                "filename": f"HHF_Acknowledgment_{donation_id[:8]}.pdf",
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            }],
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Receipt email error for {email}: {e}")
        return False


async def send_consolidated_80g_email(donor: dict, pdf_bytes: bytes, fy_label: str,
                                       fy_start, fy_end, total_amount: int, donation_count: int) -> bool:
    """Email the donor their LEGAL 80G consolidated tax certificate for the FY.
    Sent once a year (1 April for the prior FY)."""
    import base64
    api_key = os.environ.get("RESEND_API_KEY", "")
    email = (donor.get("email") or "").strip().lower()
    if not api_key or not resend or not email:
        logger.info(f"[80G MOCK] would email {email} consolidated 80G ({len(pdf_bytes)} bytes)")
        return False
    try:
        resend.api_key = api_key
        donor_name = donor.get("name", "")
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"Your 80G Tax Certificate — FY {fy_label} — Heroic HIFI Foundation",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:580px;margin:0 auto;padding:20px;">
                <h2 style="color:#1E56A0;margin:0 0 4px;">Heroic HIFI Foundation</h2>
                <p style="color:#666;font-size:12px;margin:0 0 18px;">Section 8 Non-Profit Organization, India</p>
                <p style="font-size:14px;line-height:1.65;">
                    Dear {donor_name or 'Donor'},<br/><br/>
                    Thank you for standing with us throughout <strong>FY {fy_label}</strong>.
                    Your <strong>consolidated 80G tax certificate</strong> is attached to this email and is now ready for your income tax filing.
                </p>
                <div style="background:#F0FDF4;border:1.5px solid #86EFAC;border-radius:12px;padding:16px;margin:18px 0;">
                    <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#15803D;letter-spacing:0.06em;">
                        ✓ ELIGIBLE FOR 80G TAX DEDUCTION
                    </p>
                    <p style="margin:0 0 4px;font-size:13px;color:#0D2847;">Total contributions: <strong>₹{total_amount:,}</strong></p>
                    <p style="margin:0;font-size:13px;color:#0D2847;">Number of donations: <strong>{donation_count}</strong></p>
                    <p style="margin:8px 0 0;font-size:12px;color:#475569;">Period: 1 April {fy_start.year} – 31 March {fy_end.year}</p>
                </div>
                <p style="font-size:13px;color:#475569;line-height:1.6;">
                    The attached certificate is the <strong>only document</strong> you need to claim a 50% tax deduction
                    under Section 80G of the Income Tax Act, 1961. Please retain it with your tax records.
                </p>
                <p style="font-size:12px;color:#94a3b8;margin-top:24px;">
                    With deepest gratitude,<br/>The Heroic HIFI Team
                </p>
            </div>
            """,
            "attachments": [{
                "filename": f"HHF_80G_Certificate_FY{fy_label}.pdf",
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            }],
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Consolidated 80G email error for {email}: {e}")
        return False
