import io
import os
from datetime import datetime, date, timezone, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

from utils.money import amount_in_words

# India Standard Time for FY calculations
IST = timezone(timedelta(hours=5, minutes=30))
NAVY = HexColor("#1E56A0")
SKY = HexColor("#28A9E2")
ORANGE = HexColor("#FF7F00")
DARK = HexColor("#0D2847")
GRAY = HexColor("#666666")
RED = HexColor("#B91C1C")
GREEN = HexColor("#15803D")


# ── Register a Unicode font so ₹ (U+20B9) renders correctly ──
_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
_BODY_FONT = "Helvetica"
_BODY_BOLD = "Helvetica-Bold"
try:
    _regular = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
    _bold = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")
    if os.path.exists(_regular) and os.path.exists(_bold):
        pdfmetrics.registerFont(TTFont("DejaVuSans", _regular))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", _bold))
        _BODY_FONT = "DejaVuSans"
        _BODY_BOLD = "DejaVuSans-Bold"
except Exception:
    # Fall back to Helvetica if font registration fails for any reason
    pass


def _money(amount) -> str:
    """Currency string with Rupee symbol that renders only when a Unicode font
    is available. Falls back to unambiguous ``INR`` prefix otherwise so donors
    never mistake amounts for US dollars."""
    try:
        amt = int(amount or 0)
    except (TypeError, ValueError):
        amt = 0
    if _BODY_FONT == "DejaVuSans":
        return f"\u20B9 {amt:,}"
    return f"INR {amt:,}"


def fy_for_date(d: date) -> tuple[date, date, str]:
    """Return (fy_start, fy_end, label) for the FY that contains the given date.
    Indian FY runs 1 Apr -> 31 Mar."""
    if d.month >= 4:
        start = date(d.year, 4, 1)
        end = date(d.year + 1, 3, 31)
    else:
        start = date(d.year - 1, 4, 1)
        end = date(d.year, 3, 31)
    label = f"{start.year}-{str(end.year)[-2:]}"  # e.g. "2025-26"
    return start, end, label


def _draw_letterhead(c, w, h, title: str, subtitle: str = ""):
    """Common header: org branding + title."""
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.rect(20*mm, 20*mm, w - 40*mm, h - 40*mm)
    c.setStrokeColor(SKY)
    c.setLineWidth(1)
    c.rect(22*mm, 22*mm, w - 44*mm, h - 44*mm)

    y = h - 45*mm
    c.setFont(_BODY_BOLD, 18)
    c.setFillColor(NAVY)
    c.drawCentredString(w/2, y, "HEROIC HIFI FOUNDATION")
    y -= 7*mm
    c.setFont(_BODY_FONT, 9)
    c.setFillColor(GRAY)
    c.drawCentredString(w/2, y, "Section 8 Company under The Companies Act, 2013")
    y -= 5*mm
    c.drawCentredString(w/2, y, "CIN: U88900BR2024NPL072593")
    y -= 5*mm
    c.setFont(_BODY_FONT, 7.5)
    c.drawCentredString(w/2, y, "C/o Nirbhay Kr. Agnihotry, Village: Korha, Tola: Korha, Mirjanhat, Bhagalpur, Jagdishpur, Bihar 812005")

    y -= 12*mm
    c.setStrokeColor(ORANGE)
    c.setLineWidth(2)
    c.line(35*mm, y, w - 35*mm, y)

    y -= 10*mm
    c.setFont(_BODY_BOLD, 16)
    c.setFillColor(DARK)
    c.drawCentredString(w/2, y, title)
    if subtitle:
        y -= 6*mm
        c.setFont(_BODY_FONT, 9)
        c.setFillColor(GRAY)
        c.drawCentredString(w/2, y, subtitle)
    return y


def generate_provisional_receipt_pdf(donation: dict) -> bytes:
    """Per-donation acknowledgment. Explicitly NOT a tax-deduction document.
    Donors get this on every confirmed donation; the consolidated 80G
    certificate is issued separately on 1 April for the prior FY."""
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    y = _draw_letterhead(c, w, h, "DONATION ACKNOWLEDGMENT", "(Provisional — NOT a tax certificate)")

    # TOP-OF-PAGE WARNING BAND — impossible to miss
    band_top = y - 10*mm
    band_h = 14*mm
    c.setFillColor(RED)
    c.rect(35*mm, band_top - band_h, w - 70*mm, band_h, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont(_BODY_BOLD, 11)
    c.drawCentredString(w/2, band_top - 6*mm, "THIS DOCUMENT CANNOT BE TREATED AS A TAX PAPER")
    c.setFont(_BODY_FONT, 8)
    c.drawCentredString(w/2, band_top - 10.5*mm, "Not valid for claiming a deduction under Section 80G of the Income Tax Act, 1961.")
    y = band_top - band_h - 10*mm

    receipt_no = f"HHF-ACK/{datetime.now(IST).strftime('%Y%m')}/{donation['id'][:8].upper()}"
    c.setFont(_BODY_BOLD, 9)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, f"Receipt No: {receipt_no}")
    donation_dt = donation.get("created_at", "")[:10] or datetime.now(IST).strftime("%Y-%m-%d")
    c.drawRightString(w - 35*mm, y, f"Date: {donation_dt}")

    y -= 12*mm
    fields = [
        ("Donor Name", donation.get("name", "")),
        ("PAN Number", donation.get("pan_number", "")),
        ("Email", donation.get("email", "")),
        ("Phone", donation.get("phone", "")),
        ("Amount Received", _money(donation.get('amount', 0))),
        ("Amount in Words", amount_in_words(donation.get('amount', 0))),
        ("Donation Type", donation.get("message", "") or "One-time donation"),
        ("Payment Reference", donation.get("razorpay_payment_id", "") or "—"),
        ("Confirmation Status", str(donation.get("status", "pending")).upper()),
    ]
    for label, value in fields:
        c.setFont(_BODY_BOLD, 9)
        c.setFillColor(NAVY)
        c.drawString(35*mm, y, f"{label}:")
        c.setFont(_BODY_FONT, 9)
        c.setFillColor(DARK)
        val_str = str(value)
        if len(val_str) > 70:
            val_str = val_str[:70] + "..."
        c.drawString(80*mm, y, val_str)
        y -= 7*mm

    # Compute FY of the donation + consolidated cert date
    try:
        d = datetime.fromisoformat(donation_dt).date()
    except Exception:
        d = datetime.now(IST).date()
    fy_start, fy_end, fy_label = fy_for_date(d)
    consolidated_date = date(fy_end.year, 4, 1)  # 1 April of the next FY

    # Detailed legal notice box
    y -= 6*mm
    c.setStrokeColor(RED)
    c.setLineWidth(1.5)
    box_top = y
    box_h = 46*mm
    c.rect(35*mm, y - box_h, w - 70*mm, box_h)
    # Fill with pale red
    c.setFillColor(HexColor("#FEF2F2"))
    c.rect(35.5*mm, y - box_h + 0.5*mm, w - 71*mm, box_h - 1*mm, fill=1, stroke=0)
    c.setFillColor(DARK)
    y -= 6*mm
    c.setFont(_BODY_BOLD, 10)
    c.setFillColor(RED)
    c.drawCentredString(w/2, y, "LEGAL DISCLAIMER — PLEASE READ")
    y -= 7*mm

    style = ParagraphStyle(
        "notice", fontName=_BODY_FONT, fontSize=8.5, leading=12,
        textColor=DARK, alignment=TA_LEFT,
    )
    notice_text = (
        "This acknowledgment is a <b>provisional confirmation of receipt</b> only. "
        "It <b>CANNOT be treated as a tax paper</b> and <b>cannot be used to claim a tax deduction</b> "
        "under Section 80G of the Income Tax Act, 1961, or any other provision of Indian tax law. "
        "A <b>consolidated 80G tax certificate</b> aggregating every confirmed donation made by you during "
        f"<b>Financial Year {fy_label}</b> (1 April {fy_start.year} to 31 March {fy_end.year}) "
        f"will be <b>auto-emailed to you on {consolidated_date.strftime('%d %B %Y')}</b> — the first day "
        "of the subsequent Financial Year. Please retain only that document for your income tax filing."
    )
    p = Paragraph(notice_text, style)
    pw, ph = p.wrap(w - 80*mm, 100*mm)
    p.drawOn(c, 40*mm, y - ph)
    y = box_top - box_h - 10*mm

    # Thank-you signature block
    c.setFont(_BODY_BOLD, 9)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "With heartfelt gratitude,")
    y -= 6*mm
    c.setFont(_BODY_FONT, 9)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, "Heroic HIFI Foundation")
    c.drawRightString(w - 35*mm, y, "Email: hhf.hifi@proton.me | Phone: (+91) 9060460224")

    c.save()
    buf.seek(0)
    return buf.read()


def generate_consolidated_80g_pdf(donor: dict, donations: list, fy_label: str,
                                  fy_start: date, fy_end: date) -> bytes:
    """The legal 80G certificate, issued once a year aggregating every donation
    a donor made during the FY. THIS is the document the donor uses for tax filing."""
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    y = _draw_letterhead(
        c, w, h,
        "80G TAX EXEMPTION CERTIFICATE",
        f"FY {fy_label} | 1 April {fy_start.year} to 31 March {fy_end.year}",
    )

    cert_no = f"HHF-80G/{fy_label}/{(donor.get('email', '') or 'X')[:6].upper()}"
    y -= 12*mm
    c.setFont(_BODY_BOLD, 9)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, f"Certificate No: {cert_no}")
    c.drawRightString(w - 35*mm, y, f"Issued: {datetime.now(IST).strftime('%d %B %Y')}")

    # Donor block
    y -= 12*mm
    donor_fields = [
        ("Donor Name", donor.get("name", "")),
        ("PAN Number", donor.get("pan_number", "")),
        ("Address", donor.get("address", "") or "N/A"),
        ("Email", donor.get("email", "")),
    ]
    for label, value in donor_fields:
        c.setFont(_BODY_BOLD, 9)
        c.setFillColor(NAVY)
        c.drawString(35*mm, y, f"{label}:")
        c.setFont(_BODY_FONT, 9)
        c.setFillColor(DARK)
        val_str = str(value)
        if len(val_str) > 80:
            val_str = val_str[:80] + "..."
        c.drawString(80*mm, y, val_str)
        y -= 7*mm

    # Itemised donations
    y -= 6*mm
    c.setStrokeColor(SKY)
    c.setLineWidth(0.5)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 7*mm
    c.setFont(_BODY_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "Donations during the Financial Year")
    y -= 8*mm
    c.setFont(_BODY_BOLD, 8.5)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, "Date")
    c.drawString(70*mm, y, "Reference")
    c.drawString(120*mm, y, "Mode")
    c.drawRightString(w - 35*mm, y, "Amount (INR \u20B9)")
    y -= 4*mm
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.3)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 5*mm

    total = 0
    c.setFont(_BODY_FONT, 8.5)
    c.setFillColor(DARK)
    for d in donations:
        if y < 60*mm:
            c.showPage()
            _draw_letterhead(c, w, h, "80G TAX EXEMPTION CERTIFICATE (continued)", f"FY {fy_label}")
            y = h - 80*mm
        amount = d.get("amount", 0) or 0
        total += amount
        c.drawString(35*mm, y, d.get("created_at", "")[:10])
        ref = (d.get("razorpay_payment_id", "") or d.get("id", ""))[:18]
        c.drawString(70*mm, y, ref)
        mode = "Recurring" if d.get("subscription_id") else "One-time"
        c.drawString(120*mm, y, mode)
        c.drawRightString(w - 35*mm, y, f"{amount:,}")
        y -= 6*mm

    # Total
    y -= 2*mm
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 7*mm
    c.setFont(_BODY_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, f"Total contributions in FY {fy_label}:")
    c.setFillColor(GREEN)
    c.drawRightString(w - 35*mm, y, _money(total))

    # Amount in words
    y -= 7*mm
    c.setFont(_BODY_BOLD, 9)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "In Words:")
    c.setFont(_BODY_FONT, 9)
    c.setFillColor(DARK)
    words_str = amount_in_words(total)
    if len(words_str) > 90:
        words_str = words_str[:87] + "..."
    c.drawString(57*mm, y, words_str)

    # 80G legal block
    y -= 14*mm
    c.setStrokeColor(GREEN)
    c.setLineWidth(1)
    box_h = 38*mm
    c.rect(35*mm, y - box_h, w - 70*mm, box_h)
    y -= 6*mm
    c.setFont(_BODY_BOLD, 10)
    c.setFillColor(GREEN)
    c.drawCentredString(w/2, y, "ELIGIBLE FOR 80G TAX DEDUCTION")
    y -= 6*mm

    style = ParagraphStyle(
        "legal", fontName=_BODY_FONT, fontSize=8.5, leading=12,
        textColor=DARK, alignment=TA_LEFT,
    )
    legal_text = (
        f"This is to certify that the above donations totalling <b>{_money(total)}</b> "
        f"(<b>{amount_in_words(total)}</b>) were received from "
        f"<b>{donor.get('name', '')}</b> (PAN: <b>{donor.get('pan_number', '')}</b>) during "
        f"the Financial Year <b>{fy_label}</b>. "
        "Heroic HIFI Foundation is registered under <b>Section 80G of the Income Tax Act, 1961</b>, "
        "and contributions made by the donor are eligible for a <b>50% tax deduction</b> under the said section, "
        "subject to the limits and conditions specified therein. "
        "This certificate is issued in compliance with Rule 18AB and Form 10BD requirements."
    )
    p = Paragraph(legal_text, style)
    pw, ph = p.wrap(w - 80*mm, 100*mm)
    p.drawOn(c, 40*mm, y - ph)
    y -= ph + 14*mm

    # Authorised signatory
    if y < 40*mm:
        c.showPage()
        y = h - 60*mm
    c.setFont(_BODY_BOLD, 9)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "For Heroic HIFI Foundation")
    y -= 12*mm
    c.setFont(_BODY_FONT, 8)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, "Authorised Signatory")
    c.drawRightString(w - 35*mm, y, "Email: hhf.hifi@proton.me | Phone: (+91) 9060460224")

    c.save()
    buf.seek(0)
    return buf.read()


# ── Backwards-compat alias for any caller still using the old name ──
def generate_80g_pdf(donation: dict) -> bytes:
    """Deprecated: returns the new provisional receipt for legacy callers."""
    return generate_provisional_receipt_pdf(donation)


def generate_agm_report_pdf(
    fy_label: str,
    fy_start: date,
    fy_end: date,
    tenures: list,
    generated_by: str,
) -> bytes:
    """AGM Governance Report — lists every office-bearer tenure active at any
    point in the given Indian FY (1 Apr -> 31 Mar). Used at Annual General
    Meetings and for MCA/Income-Tax filings."""
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    y = _draw_letterhead(
        c, w, h,
        "AGM GOVERNANCE REPORT",
        f"Indian FY {fy_label}  |  1 Apr {fy_start.year}  —  31 Mar {fy_end.year}",
    )
    y -= 12*mm
    c.setFont(_BODY_BOLD, 9)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, f"Generated: {datetime.now(IST).strftime('%d %b %Y, %H:%M IST')}")
    c.drawRightString(w - 35*mm, y, f"Prepared by: {generated_by}")

    y -= 10*mm
    c.setFont(_BODY_BOLD, 11)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "Office-Bearer Tenures during this FY")
    y -= 3*mm
    c.setStrokeColor(ORANGE)
    c.setLineWidth(1.5)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 8*mm

    if not tenures:
        c.setFont(_BODY_FONT, 10)
        c.setFillColor(GRAY)
        c.drawString(35*mm, y, "No office-bearer activity recorded for this Financial Year.")
    else:
        # Table header
        c.setFont(_BODY_BOLD, 9)
        c.setFillColor(DARK)
        c.drawString(35*mm, y, "Post")
        c.drawString(75*mm, y, "Office Bearer")
        c.drawString(125*mm, y, "Start")
        c.drawString(150*mm, y, "End")
        y -= 3*mm
        c.setStrokeColor(GRAY)
        c.setLineWidth(0.3)
        c.line(35*mm, y, w - 35*mm, y)
        y -= 6*mm
        c.setFont(_BODY_FONT, 9)

        for t in tenures:
            if y < 40*mm:
                c.showPage()
                _draw_letterhead(c, w, h, "AGM GOVERNANCE REPORT (continued)", f"FY {fy_label}")
                y = h - 80*mm
            post = t.get("post", "")
            name = t.get("user_name", "") or t.get("user_email", "")
            start = t.get("start_date") or "—"
            end = t.get("end_date") or "In office"
            c.setFillColor(NAVY if post in ("Chairman", "Secretary", "Treasurer") else DARK)
            c.drawString(35*mm, y, post)
            c.setFillColor(DARK)
            nm = name if len(name) <= 28 else (name[:27] + "…")
            c.drawString(75*mm, y, nm)
            c.drawString(125*mm, y, start)
            c.setFillColor(GREEN if end == "In office" else RED)
            c.drawString(150*mm, y, end)
            c.setFillColor(DARK)
            y -= 5*mm
            reason_bits = []
            if t.get("start_reason"):
                reason_bits.append(f"Assumed: {t['start_reason']}")
            if t.get("end_reason"):
                reason_bits.append(f"Left: {t['end_reason']}")
            if reason_bits:
                c.setFont(_BODY_FONT, 7.5)
                c.setFillColor(GRAY)
                note = "  ·  ".join(reason_bits)
                note = note if len(note) <= 130 else (note[:128] + "…")
                c.drawString(40*mm, y, note)
                c.setFont(_BODY_FONT, 9)
                c.setFillColor(DARK)
                y -= 5*mm
            y -= 1*mm

    # Signature block
    if y < 60*mm:
        c.showPage()
        _draw_letterhead(c, w, h, "AGM GOVERNANCE REPORT (continued)", f"FY {fy_label}")
        y = h - 80*mm
    y -= 16*mm
    c.setFont(_BODY_BOLD, 9)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "For Heroic HIFI Foundation")
    y -= 12*mm
    c.setFont(_BODY_FONT, 8)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, "Authorised Signatory")
    c.drawRightString(w - 35*mm, y, "Email: hhf.hifi@proton.me | Phone: (+91) 9060460224")

    c.save()
    buf.seek(0)
    return buf.read()


# ── Letter of Appointment PDF ──
def generate_appointment_letter_pdf(*, appointee_name: str, post: str,
                                    start_date_iso: str, leadership_bio: str = "",
                                    issued_by_name: str = "", issued_by_post: str = "",
                                    appointment_id: str = "") -> bytes:
    """Formal letter of appointment for Office Bearers (Chairman, Secretary,
    Treasurer, Event Incharge, Assistant). Generated automatically by the
    Master Admin assignment flow and emailed to the appointee."""
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    _draw_letterhead(c, w, h, "LETTER OF APPOINTMENT", post.upper())

    def fmt_iso(iso: str) -> str:
        if not iso:
            return "—"
        try:
            d = datetime.fromisoformat(iso.replace("Z", "+00:00")).date() if "T" in iso else date.fromisoformat(iso)
            return d.strftime("%d-%m-%Y")
        except Exception:
            return iso

    today_str = datetime.now(IST).date().strftime("%d-%m-%Y")
    start_str = fmt_iso(start_date_iso)

    y = h - 95*mm
    c.setFont(_BODY_FONT, 9)
    c.setFillColor(DARK)
    c.drawRightString(w - 35*mm, y, f"Dated: {today_str}")
    if appointment_id:
        c.setFillColor(GRAY)
        c.setFont(_BODY_FONT, 7.5)
        c.drawString(35*mm, y, f"Ref: {appointment_id[:18]}")
        c.setFont(_BODY_FONT, 9)
        c.setFillColor(DARK)

    y -= 14*mm
    c.setFont(_BODY_BOLD, 11)
    c.drawString(35*mm, y, "To,")
    y -= 6*mm
    c.setFont(_BODY_FONT, 11)
    c.drawString(35*mm, y, f"{appointee_name},")
    y -= 6*mm
    c.setFillColor(GRAY)
    c.setFont(_BODY_FONT, 9)
    c.drawString(35*mm, y, "(Through electronic delivery)")

    y -= 14*mm
    c.setFont(_BODY_BOLD, 11)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, f"Subject: Appointment as {post}, Heroic HIFI Foundation")

    y -= 14*mm
    body_text = (
        f"Dear {appointee_name},<br/><br/>"
        f"On behalf of the Board of <b>Heroic HIFI Foundation</b>, it is my privilege to formally "
        f"convey our unanimous decision to appoint you as the <b>{post}</b> of the Foundation, "
        f"with effect from <b>{start_str}</b>."
        "<br/><br/>"
        "This appointment is made in recognition of the dedication, integrity and stewardship you "
        "have shown towards the Foundation's mission of building a more compassionate, equitable and "
        "empowered society. By accepting this office you agree to:"
        "<br/><br/>"
        "&nbsp;&nbsp;1. Uphold the values, byelaws and constitutional framework of the Foundation at all times.<br/>"
        f"&nbsp;&nbsp;2. Discharge the duties of the office of <b>{post}</b> with diligence, transparency and the highest fiduciary standards.<br/>"
        "&nbsp;&nbsp;3. Maintain the confidentiality of all sensitive information accessed in the course of this office.<br/>"
        "&nbsp;&nbsp;4. Cooperate fully with statutory audits, AGM proceedings, and Income Tax / Section 8 compliance under the Companies Act, 2013."
    )
    if leadership_bio:
        body_text += f"<br/><br/><i>&ldquo;{leadership_bio}&rdquo;</i>"
    body_text += (
        "<br/><br/>"
        "Your tenure shall be governed by the Foundation's tenure-tracking ledger and may be honourably "
        "concluded as per due process. We are confident that under your stewardship, the Foundation will "
        "continue to touch lives meaningfully, in keeping with our motto: "
        "<i>service before self, dignity for all</i>."
        "<br/><br/>"
        "With warm regards and heartfelt gratitude,"
    )
    para_style = ParagraphStyle(
        name="appt-body", fontName=_BODY_FONT, fontSize=10.5, leading=15,
        textColor=DARK, alignment=TA_LEFT,
    )
    para = Paragraph(body_text, para_style)
    _aw, ah = para.wrap(w - 70*mm, y - 70*mm)
    para.drawOn(c, 35*mm, y - ah)
    y -= ah + 8*mm

    if y < 70*mm:
        c.showPage()
        _draw_letterhead(c, w, h, "LETTER OF APPOINTMENT (continued)", post.upper())
        y = h - 100*mm
    y -= 20*mm
    c.setFont(_BODY_BOLD, 10)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "For Heroic HIFI Foundation")
    y -= 14*mm
    c.setFont(_BODY_BOLD, 10)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, issued_by_name or "Authorised Signatory")
    if issued_by_post:
        y -= 5*mm
        c.setFont(_BODY_FONT, 9)
        c.setFillColor(GRAY)
        c.drawString(35*mm, y, issued_by_post)

    y -= 18*mm
    c.setStrokeColor(ORANGE)
    c.setLineWidth(0.8)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 6*mm
    c.setFont(_BODY_FONT, 7.5)
    c.setFillColor(GRAY)
    c.drawString(35*mm, y, "Auto-generated on the date hereof. This letter is electronically issued and does not require a wet-ink signature.")
    y -= 4*mm
    c.drawString(35*mm, y, "Email: hhf.hifi@proton.me  \u00b7  Phone: (+91) 9060460224  \u00b7  Section 8 Non-Profit  \u00b7  Bhagalpur, Bihar")

    c.save()
    buf.seek(0)
    return buf.read()

