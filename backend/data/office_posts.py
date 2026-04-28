"""Canonical office-bearer posts for Heroic HIFI Foundation.

Only the Master Admin (``is_super_admin``) can attach or remove a post.
Posts in ``UNIQUE_POSTS`` can be held by **at most one** person at a time —
the backend blocks double-assignment with HTTP 400. ``Assistant`` is the
only post that can be held by many people simultaneously.
"""

OFFICE_POSTS: list[str] = [
    "Chairman",
    "Secretary",
    "Treasurer",
    "Assistant",
]

# Posts that may only be held by a single user at any time.
UNIQUE_POSTS: set[str] = {"Chairman", "Secretary", "Treasurer"}

OFFICE_POSTS_SET = set(OFFICE_POSTS)
