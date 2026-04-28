from fastapi import APIRouter, HTTPException, Request, Depends
import os
import uuid
from datetime import datetime, timezone

from config import db
from models.schemas import DonationInput
from utils.auth import get_current_user
from utils.activity import log_activity
from routes.certificates import generate_provisional_receipt_pdf
import io
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api")


@router.post("/donations/create-order")
async def create_razorpay_order(data: DonationInput, request: Request, user: dict = Depends(get_current_user)):
    # Razorpay charges ~2% + 18% GST on the fee = effective 2.36%. We round up
    # to the next rupee so the foundation always nets the full pledge.
    import math
    fee_covered = math.ceil(data.amount * 0.0236) if data.cover_fee else 0
    gross_amount = data.amount + fee_covered
    doc = {
        "id": str(uuid.uuid4()), "name": data.name, "email": data.email.lower().strip(),
        "phone": data.phone,
        "amount": data.amount,           # the donor's pledge — what HHF receives, what 80G claims
        "fee_covered": fee_covered,      # the donor's voluntary top-up to absorb Razorpay's fee
        "gross_amount": gross_amount,    # the actual amount Razorpay charges
        "pan_number": data.pan_number,
        "aadhaar_number": data.aadhaar_number or "", "address": data.address or "",
        "message": data.message or "", "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    rz_key = os.environ.get("RAZORPAY_KEY_ID")
    rz_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not rz_key or not rz_secret:
        await db.donations.insert_one(doc)
        doc.pop("_id", None)
        await log_activity("donation_recorded", "donation", doc["id"], data.email, f"Amount: {data.amount} (no Razorpay keys)", request.client.host if request.client else "")
        return {"donation": doc, "message": "Donation recorded. Razorpay keys not configured yet."}
    import razorpay
    rz_client = razorpay.Client(auth=(rz_key, rz_secret))
    order = rz_client.order.create(data={"amount": gross_amount * 100, "currency": "INR", "receipt": doc["id"]})
    doc["razorpay_order_id"] = order["id"]
    await db.donations.insert_one(doc)
    doc.pop("_id", None)
    note = f"Pledge: {data.amount}, gross charged: {gross_amount} (fee absorbed: {fee_covered})"
    await log_activity("razorpay_order_created", "donation", doc["id"], data.email, note, request.client.host if request.client else "")
    return {"donation": doc, "razorpay_order_id": order["id"], "razorpay_key": rz_key, "amount": gross_amount * 100, "currency": "INR"}


@router.post("/donations/verify-payment")
async def verify_payment(body: dict, request: Request, user: dict = Depends(get_current_user)):
    rz_key = os.environ.get("RAZORPAY_KEY_ID")
    rz_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not rz_key or not rz_secret:
        raise HTTPException(status_code=500, detail="Razorpay not configured")
    import razorpay
    rz_client = razorpay.Client(auth=(rz_key, rz_secret))
    try:
        rz_client.utility.verify_payment_signature({
            "razorpay_order_id": body["razorpay_order_id"],
            "razorpay_payment_id": body["razorpay_payment_id"],
            "razorpay_signature": body["razorpay_signature"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    await db.donations.update_one(
        {"razorpay_order_id": body["razorpay_order_id"]},
        {"$set": {"status": "confirmed", "razorpay_payment_id": body["razorpay_payment_id"]}},
    )
    # Real-time Top-Donor recompute once the payment is verified by Razorpay.
    try:
        from utils.top_donor import recompute_top_donor
        await recompute_top_donor()
    except Exception:
        pass
    # Real-time Most-Generous-Donor recompute (fee-cover ladder).
    try:
        from utils.most_generous import recompute_most_generous
        await recompute_most_generous()
    except Exception:
        pass
    # Email the provisional receipt only AFTER Razorpay has confirmed the payment
    donation = await db.donations.find_one({"razorpay_order_id": body["razorpay_order_id"]}, {"_id": 0})
    receipt_sent = False
    if donation and donation.get("pan_number"):
        try:
            from utils.email import send_donation_receipt_email
            pdf = generate_provisional_receipt_pdf(donation)
            receipt_sent = await send_donation_receipt_email(donation, pdf, label="donation")
        except Exception:
            pass
    await log_activity("payment_verified", "donation", body["razorpay_order_id"], (donation or {}).get("email", ""),
                       f"amount=₹{(donation or {}).get('amount', 0)} receipt_sent={receipt_sent}",
                       request.client.host if request.client else "")
    return {"message": "Payment verified successfully", "receipt_sent": receipt_sent}


@router.post("/donations")
async def create_donation(data: DonationInput, request: Request):
    doc = {
        "id": str(uuid.uuid4()), "name": data.name, "email": data.email.lower().strip(),
        "phone": data.phone, "amount": data.amount, "pan_number": data.pan_number,
        "aadhaar_number": data.aadhaar_number or "", "address": data.address or "",
        "message": data.message or "", "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.donations.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("donation_recorded", "donation", doc["id"], data.email, f"Amount: {data.amount}", request.client.host if request.client else "")
    return {"message": "Donation recorded successfully.", "donation": doc}


@router.get("/donations")
async def list_donations(user: dict = Depends(get_current_user)):
    return await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.get("/donations/mine")
async def list_my_donations(user: dict = Depends(get_current_user)):
    """Return the signed-in donor's own donations (latest first), with cover-fee details."""
    email = (user.get("email") or "").lower().strip()
    rows = await db.donations.find({"email": email}, {"_id": 0}).sort("created_at", -1).to_list(200)
    # Defensive defaults so old records (pre-Cover-Fee) render cleanly.
    for r in rows:
        r.setdefault("fee_covered", 0)
        r.setdefault("gross_amount", r.get("amount", 0))
    return rows


@router.get("/donations/{donation_id}/certificate")
async def download_provisional_receipt(donation_id: str):
    donation = await db.donations.find_one({"id": donation_id}, {"_id": 0})
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    # Gate: provisional receipt is ONLY downloadable after Razorpay confirms the payment.
    status = donation.get("status", "pending")
    if status != "confirmed":
        raise HTTPException(
            status_code=409,
            detail=f"Receipt unavailable: payment status is '{status}'. Receipts are issued only after Razorpay confirms the transaction.",
        )
    if not donation.get("pan_number"):
        raise HTTPException(status_code=400, detail="PAN number is required on the donation record")
    pdf_bytes = generate_provisional_receipt_pdf(donation)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=HHF_Acknowledgment_{donation_id[:8]}.pdf"},
    )
