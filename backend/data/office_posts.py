"""Canonical office-bearer posts for a Section-8 / Non-Profit organisation.
Only the Master Admin (``is_super_admin``) can attach or remove a post from
a user profile. The list is intentionally conservative and mirrors common
positions used by Indian NGOs so auditors and donors recognise them.
"""

OFFICE_POSTS: list[str] = [
    # Founders & executive leadership
    "Founder",
    "Co-Founder",
    "President",
    "Vice President",
    # Statutory office bearers
    "General Secretary",
    "Joint Secretary",
    "Treasurer",
    "Joint Treasurer",
    # Trustees & board
    "Managing Trustee",
    "Trustee",
    "Board Member",
    "Independent Director",
    # Operational leadership
    "Executive Director",
    "Programme Director",
    "Chief Operating Officer",
    "Chief Financial Officer",
    # Functional heads
    "Programme Manager",
    "Volunteer Coordinator",
    "Fundraising Lead",
    "Communications Lead",
    "Partnerships Lead",
    # Advisory
    "Advisor",
    "Legal Advisor",
    "Mentor",
    "Auditor",
]

OFFICE_POSTS_SET = set(OFFICE_POSTS)
