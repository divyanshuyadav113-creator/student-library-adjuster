"""
fines.py
All fine-calculation logic lives here so the rules are defined in one
place and are easy to unit test / tweak for a resume demo.
"""

from datetime import datetime, date

# ---- Configurable fine policy -------------------------------------------
LOAN_PERIOD_DAYS = 14        # how many days a member may keep a book
GRACE_PERIOD_DAYS = 0        # days after due date before fines start
FINE_PER_DAY = 5.0           # currency units charged per overdue day
MAX_FINE = 200.0             # fine is capped so it never runs away
# --------------------------------------------------------------------------


def calculate_due_date(issue_date: date) -> date:
    """Given an issue date, return the date the book is due."""
    from datetime import timedelta
    return issue_date + timedelta(days=LOAN_PERIOD_DAYS)


def days_overdue(due_date: date, as_of: date = None) -> int:
    """Number of days a book is overdue as of a given date (default: today).
    Returns 0 if not yet overdue."""
    as_of = as_of or date.today()
    delta = (as_of - due_date).days
    return max(0, delta - GRACE_PERIOD_DAYS)


def calculate_fine(due_date: date, return_date: date = None) -> float:
    """Core fine calculator.

    - due_date: when the book was supposed to be returned
    - return_date: when it actually was (or will be) returned; defaults
      to today, which lets the dashboard show a 'fine so far' figure for
      books that are still checked out.
    """
    check_date = return_date or date.today()
    overdue = days_overdue(due_date, check_date)
    fine = round(overdue * FINE_PER_DAY, 2)
    return min(fine, MAX_FINE)


def parse_date(value: str) -> date:
    """Helper: 'YYYY-MM-DD' string -> date object."""
    return datetime.strptime(value, "%Y-%m-%d").date()


def fine_breakdown(due_date_str: str, return_date_str: str = None) -> dict:
    """Returns a dict with everything a UI needs to display a fine, used
    by both the dashboard and the return-book screen."""
    due = parse_date(due_date_str)
    ret = parse_date(return_date_str) if return_date_str else None
    overdue_days = days_overdue(due, ret or date.today())
    fine = calculate_fine(due, ret)
    return {
        "due_date": due_date_str,
        "checked_against": (ret or date.today()).isoformat(),
        "overdue_days": overdue_days,
        "rate_per_day": FINE_PER_DAY,
        "fine_amount": fine,
        "capped": fine >= MAX_FINE,
    }
