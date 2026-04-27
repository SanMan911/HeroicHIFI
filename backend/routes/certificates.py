import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle


def generate_80g_pdf(donation: dict) -> bytes:
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    navy = HexColor("#1E56A0")
    sky = HexColor("#28A9E2")
    orange = HexColor("#FF7F00")
    dark = HexColor("#0D2847")
    gray = HexColor("#666666")

    c.setStrokeColor(navy)
    c.setLineWidth(3)
    c.rect(20*mm, 20*mm, w - 40*mm, h - 40*mm)
    c.setStrokeColor(sky)
    c.setLineWidth(1)
    c.rect(22*mm, 22*mm, w - 44*mm, h - 44*mm)

    y = h - 45*mm
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(navy)
    c.drawCentredString(w/2, y, "HEROIC HIFI FOUNDATION")
    y -= 7*mm
    c.setFont("Helvetica", 9)
    c.setFillColor(gray)
    c.drawCentredString(w/2, y, "Section 8 Company under The Companies Act, 2013")
    y -= 5*mm
    c.drawCentredString(w/2, y, "CIN: U88900BR2024NPL072593")
    y -= 5*mm
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(w/2, y, "C/o Nirbhay Kr. Agnihotry, Village: Korha, Tola: Korha, Mirjanhat, Bhagalpur, Jagdishpur, Bihar 812005")

    y -= 12*mm
    c.setStrokeColor(orange)
    c.setLineWidth(2)
    c.line(35*mm, y, w - 35*mm, y)

    y -= 10*mm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(dark)
    c.drawCentredString(w/2, y, "PROVISIONAL DONATION RECEIPT")
    y -= 7*mm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(orange)
    c.drawCentredString(w/2, y, "Under Section 80G of the Income Tax Act, 1961")
    y -= 5*mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(gray)
    c.drawCentredString(w/2, y, "(Provisional Certificate \u2014 Eligible for 50% Tax Rebate)")

    cert_no = f"HHF/{datetime.now().strftime('%Y%m')}/{donation['id'][:8].upper()}"
    y -= 12*mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(dark)
    c.drawString(35*mm, y, f"Certificate No: {cert_no}")
    c.drawRightString(w - 35*mm, y, f"Date: {datetime.now().strftime('%d %B %Y')}")

    y -= 15*mm
    fields = [
        ("Donor Name", donation.get("name", "")),
        ("PAN Number", donation.get("pan_number", "")),
        ("Aadhaar Number", donation.get("aadhaar_number", "") or "N/A"),
        ("Address", donation.get("address", "") or "N/A"),
        ("Phone", donation.get("phone", "")),
        ("Email", donation.get("email", "")),
        ("Donation Amount", f"\u20B9 {donation.get('amount', 0):,}"),
        ("Donation Date", donation.get("created_at", "")[:10]),
        ("Payment Status", donation.get("status", "pending").capitalize()),
    ]
    for label, value in fields:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(navy)
        c.drawString(35*mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.setFillColor(dark)
        val_str = str(value)
        if len(val_str) > 70:
            val_str = val_str[:70] + "..."
        c.drawString(80*mm, y, val_str)
        y -= 7*mm

    y -= 8*mm
    c.setStrokeColor(sky)
    c.setLineWidth(0.5)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 8*mm

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(dark)
    c.drawCentredString(w/2, y, "IMPORTANT NOTICE")
    y -= 6*mm
    style = ParagraphStyle("notice", fontName="Helvetica", fontSize=8, leading=11, textColor=gray, alignment=TA_LEFT)
    notice_text = (
        "This is a <b>Provisional Donation Receipt</b> issued by Heroic HIFI Foundation. "
        "As per the applicable provisions, this provisional certificate entitles the donor to claim a <b>50% tax rebate/deduction</b> "
        "on the donated amount under Section 80G of the Income Tax Act, 1961. "
        "This certificate is subject to the final approval and issuance of the regular 80G certificate by the Income Tax Department. "
        "The donor is advised to retain this receipt for their tax records."
    )
    p = Paragraph(notice_text, style)
    pw, ph = p.wrap(w - 70*mm, 100*mm)
    p.drawOn(c, 35*mm, y - ph)
    y -= ph + 15*mm

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(navy)
    c.drawString(35*mm, y, "For Heroic HIFI Foundation")
    y -= 12*mm
    c.setFont("Helvetica", 8)
    c.setFillColor(dark)
    c.drawString(35*mm, y, "Authorised Signatory")
    c.drawRightString(w - 35*mm, y, "Email: hhf.hifi@proton.me | Phone: (+91) 7970976881")

    c.save()
    buf.seek(0)
    return buf.read()
