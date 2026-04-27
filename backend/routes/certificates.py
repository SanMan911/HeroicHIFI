import io
from datetime import datetime, date, timezone, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# India Standard Time for FY calculations
IST = timezone(timedelta(hours=5, minutes=30))
NAVY = HexColor("#1E56A0")
SKY = HexColor("#28A9E2")
ORANGE = HexColor("#FF7F00")
DARK = HexColor("#0D2847")
GRAY = HexColor("#666666")
RED = HexColor("#B91C1C")
GREEN = HexColor("#15803D")


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
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(NAVY)
    c.drawCentredString(w/2, y, "HEROIC HIFI FOUNDATION")
    y -= 7*mm
    c.setFont("Helvetica", 9)
    c.setFillColor(GRAY)
    c.drawCentredString(w/2, y, "Section 8 Company under The Companies Act, 2013")
    y -= 5*mm
    c.drawCentredString(w/2, y, "CIN: U88900BR2024NPL072593")
    y -= 5*mm
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(w/2, y, "C/o Nirbhay Kr. Agnihotry, Village: Korha, Tola: Korha, Mirjanhat, Bhagalpur, Jagdishpur, Bihar 812005")

    y -= 12*mm
    c.setStrokeColor(ORANGE)
    c.setLineWidth(2)
    c.line(35*mm, y, w - 35*mm, y)

    y -= 10*mm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(DARK)
    c.drawCentredString(w/2, y, title)
    if subtitle:
        y -= 6*mm
        c.setFont("Helvetica", 9)
        c.setFillColor(GRAY)
        c.drawCentredString(w/2, y, subtitle)
    return y


def generate_provisional_receipt_pdf(donation: dict) -> bytes:
    """Per-donation acknowledgment. Explicitly NOT a tax-deduction document.
    Donors get this on every donation; the consolidated 80G certificate
    is issued separately on 1 April for the prior FY."""
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    y = _draw_letterhead(c, w, h, "DONATION ACKNOWLEDGMENT", "(Provisional Receipt — Not a Tax Certificate)")

    receipt_no = f"HHF-ACK/{datetime.now(IST).strftime('%Y%m')}/{donation['id'][:8].upper()}"
    y -= 12*mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, f"Receipt No: {receipt_no}")
    donation_dt = donation.get("created_at", "")[:10] or datetime.now(IST).strftime("%Y-%m-%d")
    c.drawRightString(w - 35*mm, y, f"Date: {donation_dt}")

    y -= 13*mm
    fields = [
        ("Donor Name", donation.get("name", "")),
        ("PAN Number", donation.get("pan_number", "")),
        ("Email", donation.get("email", "")),
        ("Phone", donation.get("phone", "")),
        ("Amount Received", f"\u20B9 {donation.get('amount', 0):,}"),
        ("Donation Type", donation.get("message", "") or "One-time donation"),
        ("Payment Reference", donation.get("razorpay_payment_id", "") or "—"),
        ("Status", str(donation.get("status", "pending")).capitalize()),
    ]
    for label, value in fields:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NAVY)
        c.drawString(35*mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
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

    # IMPORTANT NOTICE box — bold, red border, no 80G language
    y -= 6*mm
    c.setStrokeColor(RED)
    c.setLineWidth(1.2)
    box_top = y
    box_h = 38*mm
    c.rect(35*mm, y - box_h, w - 70*mm, box_h)
    y -= 6*mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(RED)
    c.drawCentredString(w/2, y, "IMPORTANT — THIS IS NOT AN 80G TAX CERTIFICATE")
    y -= 6*mm

    style = ParagraphStyle(
        "notice", fontName="Helvetica", fontSize=8.5, leading=12,
        textColor=DARK, alignment=TA_LEFT,
    )
    notice_text = (
        "This document is a <b>provisional acknowledgment</b> of your contribution and "
        "<b>cannot be used to claim a tax deduction</b> under Section 80G of the Income Tax Act, 1961. "
        f"A <b>consolidated 80G tax certificate</b> covering all your donations made during "
        f"<b>FY {fy_label} (1 April {fy_start.year} to 31 March {fy_end.year})</b> "
        f"will be auto-emailed to you on or shortly after <b>{consolidated_date.strftime('%d %B %Y')}</b>. "
        "Please retain that document — and not this receipt — for filing your income tax return."
    )
    p = Paragraph(notice_text, style)
    pw, ph = p.wrap(w - 80*mm, 100*mm)
    p.drawOn(c, 40*mm, y - ph)
    y = box_top - box_h - 8*mm

    # Thank-you signature block
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "With heartfelt gratitude,")
    y -= 6*mm
    c.setFont("Helvetica", 9)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, "Heroic HIFI Foundation")
    c.drawRightString(w - 35*mm, y, "Email: hhf.hifi@proton.me | Phone: (+91) 7970976881")

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
    c.setFont("Helvetica-Bold", 9)
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
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NAVY)
        c.drawString(35*mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
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
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "Donations during the Financial Year")
    y -= 8*mm
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, "Date")
    c.drawString(70*mm, y, "Reference")
    c.drawString(120*mm, y, "Mode")
    c.drawRightString(w - 35*mm, y, "Amount (\u20B9)")
    y -= 4*mm
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.3)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 5*mm

    total = 0
    c.setFont("Helvetica", 8.5)
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
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, f"Total contributions in FY {fy_label}:")
    c.setFillColor(GREEN)
    c.drawRightString(w - 35*mm, y, f"\u20B9 {total:,}")

    # 80G legal block
    y -= 14*mm
    c.setStrokeColor(GREEN)
    c.setLineWidth(1)
    box_h = 38*mm
    c.rect(35*mm, y - box_h, w - 70*mm, box_h)
    y -= 6*mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(GREEN)
    c.drawCentredString(w/2, y, "ELIGIBLE FOR 80G TAX DEDUCTION")
    y -= 6*mm

    style = ParagraphStyle(
        "legal", fontName="Helvetica", fontSize=8.5, leading=12,
        textColor=DARK, alignment=TA_LEFT,
    )
    legal_text = (
        f"This is to certify that the above donations totalling <b>\u20B9 {total:,}</b> were received from "
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
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(NAVY)
    c.drawString(35*mm, y, "For Heroic HIFI Foundation")
    y -= 12*mm
    c.setFont("Helvetica", 8)
    c.setFillColor(DARK)
    c.drawString(35*mm, y, "Authorised Signatory")
    c.drawRightString(w - 35*mm, y, "Email: hhf.hifi@proton.me | Phone: (+91) 7970976881")

    c.save()
    buf.seek(0)
    return buf.read()


# ── Backwards-compat alias for any caller still using the old name ──
def generate_80g_pdf(donation: dict) -> bytes:
    """Deprecated: returns the new provisional receipt for legacy callers."""
    return generate_provisional_receipt_pdf(donation)
