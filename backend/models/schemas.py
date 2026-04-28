from pydantic import BaseModel
from typing import List, Optional


class OTPRequest(BaseModel):
    email: str
    purpose: str = "registration"

class OTPVerify(BaseModel):
    email: str
    otp: str
    purpose: str = "registration"

class RegisterInput(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    age: Optional[int] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    pan_number: str
    aadhaar_number: str
    otp_token: str
    role: str = "member"
    specializations: List[str] = []

class LoginInput(BaseModel):
    email: str
    password: str

class DonationInput(BaseModel):
    name: str
    email: str
    phone: str
    amount: int
    pan_number: str
    aadhaar_number: Optional[str] = None
    address: Optional[str] = None
    message: Optional[str] = None
    otp_token: Optional[str] = None
    cover_fee: Optional[bool] = False  # Donor opts to cover Razorpay's transaction fee

class VolunteerInput(BaseModel):
    name: str
    email: str
    phone: str
    city: str
    interests: List[str] = []
    message: Optional[str] = None

class QueryInput(BaseModel):
    name: str
    email: str
    mission: str
    subject: str
    message: str

class StatusUpdate(BaseModel):
    status: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    email: str
    token: str
    new_password: str

class TicketInput(BaseModel):
    subject: str
    description: str
    priority: str = "medium"

class TicketResponse(BaseModel):
    response: str

class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    volunteer_hours: Optional[int] = None
    merchandise_issued: Optional[bool] = None
    admin_comments: Optional[str] = None
    status: Optional[str] = None
    suspended_until: Optional[str] = None
    suspension_reason: Optional[str] = None
    designation: Optional[str] = None
    leadership_bio: Optional[str] = None
    # Date of assuming OR leaving office (YYYY-MM-DD). Required whenever
    # ``designation`` is being set (start) or cleared (end). If omitted on an
    # assignment the backend defaults to today (IST).
    effective_date: Optional[str] = None


class AdminRemovalRequest(BaseModel):
    target_email: str
    reason: str = ""


class EventProposalInput(BaseModel):
    mission: str  # broad mission category, e.g. "Environment", "Hunger", "Education"
    drive_name: str  # specific drive, e.g. "Tree Plantation @ Korha Village"
    event_date: str  # YYYY-MM-DD
    place: str
    days: int = 1
    event_time: Optional[str] = None  # HH:MM (optional)
    budget: float = 0.0
    notes: Optional[str] = None


class EventEditInput(BaseModel):
    mission: Optional[str] = None
    drive_name: Optional[str] = None
    event_date: Optional[str] = None
    place: Optional[str] = None
    days: Optional[int] = None
    event_time: Optional[str] = None
    budget: Optional[float] = None
    notes: Optional[str] = None

class BadgeAction(BaseModel):
    badge: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SpecializationUpdate(BaseModel):
    specializations: List[str]

class RoleChangeRequest(BaseModel):
    requested_role: str
    reason: str = ""

class DriveInput(BaseModel):
    title: str
    description: str
    date: str
    location: str
    drive_type: str = "upcoming"
    image_url: Optional[str] = None
    mission_slug: Optional[str] = None
    estimated_days: int = 1
    time: Optional[str] = None

class MessageInput(BaseModel):
    recipient_email: str
    message: str

class EmailBlastInput(BaseModel):
    subject: str
    body: str
    target: str = "all"

class EventReportInput(BaseModel):
    drive_id: str
    time_spent: str
    resources_spent: str
    summary: str
    issues: str
    outcome: str
    admin_rating: int = 5
    attendance: List[str] = []

class AdminPromotionRequest(BaseModel):
    target_email: str
    reason: str = ""

class DeleteUserInput(BaseModel):
    reason: str

class SubscriptionInput(BaseModel):
    plan: str  # "monthly" | "quarterly" | "half_yearly" | "annual" | "custom_<interval>"
    name: str
    email: str
    phone: str
    pan_number: str
    address: Optional[str] = ""
    custom_amount: Optional[int] = None  # rupees — required when plan starts with "custom_"
    cover_fee: Optional[bool] = False  # Donor opts to cover Razorpay's transaction fee (custom plans only)

class PANVerifyInput(BaseModel):
    pan: str
    aadhaar: Optional[str] = ""
    name: str
