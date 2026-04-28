"""Privacy + display helpers for public-facing money values.

Indian rounding-down to the nearest hundred is a privacy safeguard — exact
donation amounts are NEVER shown on public surfaces (homepage marquee, Wall of
Fame, public ledgers). Donor's own profile and legal 80G certificates always
keep the EXACT amount.
"""


def round_to_100(amount) -> int:
    """Round a money value to the nearest hundred using standard
    half-up rounding (₹50 → ₹100, ₹149 → ₹100, ₹150 → ₹200). Negative
    or invalid inputs collapse to 0. Used purely for PUBLIC display —
    never call this from legal/donor-private flows."""
    try:
        n = int(amount or 0)
    except (TypeError, ValueError):
        return 0
    if n <= 0:
        return 0
    return ((n + 50) // 100) * 100


_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
]


def _two_digit(n: int) -> str:
    if n < 20:
        return _ONES[n]
    return (_TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else "")).strip()


def _three_digit(n: int) -> str:
    """0..999 → words. e.g. 105 → 'One Hundred Five'."""
    parts = []
    if n >= 100:
        parts.append(_ONES[n // 100] + " Hundred")
        n %= 100
    if n:
        parts.append(_two_digit(n))
    return " ".join(parts).strip()


def int_to_indian_words(n) -> str:
    """Render an integer as Indian-system words (lakh/crore).
    Examples:
        100        -> "One Hundred"
        1000       -> "One Thousand"
        100000     -> "One Lakh"
        10000000   -> "One Crore"
        123456     -> "One Lakh Twenty Three Thousand Four Hundred Fifty Six"
        12345678   -> "One Crore Twenty Three Lakh Forty Five Thousand Six Hundred Seventy Eight"
    """
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        return "Zero"
    if n == 0:
        return "Zero"
    if n < 0:
        return "Minus " + int_to_indian_words(-n)

    parts = []
    crore = n // 10000000
    if crore:
        parts.append(_two_digit(crore % 100))
        if crore >= 100:
            # Anything above 99 crore rolls back to <thousand-crore> notation.
            parts.insert(0, _three_digit(crore // 100) + " Hundred")
        parts.append("Crore")
        n %= 10000000
    lakh = n // 100000
    if lakh:
        parts.append(_two_digit(lakh))
        parts.append("Lakh")
        n %= 100000
    thousand = n // 1000
    if thousand:
        parts.append(_two_digit(thousand))
        parts.append("Thousand")
        n %= 1000
    if n:
        parts.append(_three_digit(n))
    return " ".join(p for p in parts if p).strip()


def amount_in_words(amount, currency: str = "Rupees") -> str:
    """User-facing 'Rupees One Hundred Only' phrasing for legal certificates."""
    return f"{currency} {int_to_indian_words(amount)} Only"
