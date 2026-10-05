"""
models.py
Data-access layer. Every function opens its own short-lived DB cursor
via database.get_cursor() and returns plain dicts, so the Flask routes
in app.py never have to touch SQL directly.
"""

from datetime import date

from database import get_cursor
from fines import calculate_due_date, calculate_fine, parse_date


# ---------------------------------------------------------------- Books --
def add_book(isbn, title, author, category, total_copies):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO books (isbn, title, author, category,
                                   total_copies, available_copies)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (isbn, title, author, category, total_copies, total_copies),
        )
        return cur.lastrowid


def set_book_qr(book_id, qr_path):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE books SET qr_path = ? WHERE id = ?", (qr_path, book_id))


def get_all_books(search=None):
    with get_cursor() as cur:
        if search:
            like = f"%{search}%"
            cur.execute(
                """SELECT * FROM books
                   WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
                   ORDER BY title""",
                (like, like, like),
            )
        else:
            cur.execute("SELECT * FROM books ORDER BY title")
        return [dict(row) for row in cur.fetchall()]


def get_book(book_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def delete_book(book_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))


def _adjust_available_copies(cur, book_id, delta):
    cur.execute(
        "UPDATE books SET available_copies = available_copies + ? WHERE id = ?",
        (delta, book_id),
    )


# -------------------------------------------------------------- Members --
def add_member(name, email, phone):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO members (name, email, phone) VALUES (?, ?, ?)",
            (name, email, phone),
        )
        return cur.lastrowid


def get_all_members():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM members ORDER BY name")
        return [dict(row) for row in cur.fetchall()]


def get_member(member_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        row = cur.fetchone()
        return dict(row) if row else None


# --------------------------------------------------------- Transactions --
def issue_book(book_id, member_id):
    """Issues a book if a copy is available. Returns (success, message)."""
    book = get_book(book_id)
    if not book:
        return False, "Book not found."
    if book["available_copies"] <= 0:
        return False, "No copies available right now."

    issue_date = date.today()
    due_date = calculate_due_date(issue_date)

    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO transactions
               (book_id, member_id, issue_date, due_date, status)
               VALUES (?, ?, ?, ?, 'ISSUED')""",
            (book_id, member_id, issue_date.isoformat(), due_date.isoformat()),
        )
        _adjust_available_copies(cur, book_id, -1)

    return True, f"Book issued. Due back {due_date.isoformat()}."


def return_book(transaction_id):
    """Marks a transaction returned, calculates the fine, and restocks
    the copy. Returns (success, message, fine_amount)."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        row = cur.fetchone()
        txn = dict(row) if row else None

    if not txn:
        return False, "Transaction not found.", 0
    if txn["status"] == "RETURNED":
        return False, "This book was already returned.", 0

    return_date = date.today()
    due = parse_date(txn["due_date"])
    fine = calculate_fine(due, return_date)

    with get_cursor(commit=True) as cur:
        cur.execute(
            """UPDATE transactions
               SET return_date = ?, fine_amount = ?, status = 'RETURNED'
               WHERE id = ?""",
            (return_date.isoformat(), fine, transaction_id),
        )
        _adjust_available_copies(cur, txn["book_id"], 1)

    msg = "Book returned." if fine == 0 else f"Book returned. Fine due: {fine}"
    return True, msg, fine


def mark_fine_paid(transaction_id):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE transactions SET fine_paid = 1 WHERE id = ?",
            (transaction_id,),
        )


def get_active_transactions():
    """All currently issued (not yet returned) transactions, with book
    and member details joined in, plus a live fine estimate."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT t.*, b.title, b.isbn, m.name AS member_name
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            JOIN members m ON m.id = t.member_id
            WHERE t.status = 'ISSUED'
            ORDER BY t.due_date
        """)
        rows = [dict(r) for r in cur.fetchall()]

    for r in rows:
        due = parse_date(r["due_date"])
        r["current_fine"] = calculate_fine(due)
        r["is_overdue"] = r["current_fine"] > 0
    return rows


def get_all_transactions():
    with get_cursor() as cur:
        cur.execute("""
            SELECT t.*, b.title, b.isbn, m.name AS member_name
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            JOIN members m ON m.id = t.member_id
            ORDER BY t.issue_date DESC
        """)
        return [dict(r) for r in cur.fetchall()]


# ------------------------------------------------------------- Dashboard --
def get_dashboard_stats():
    books = get_all_books()
    active = get_active_transactions()
    all_txns = get_all_transactions()

    total_copies = sum(b["total_copies"] for b in books)
    available_copies = sum(b["available_copies"] for b in books)
    issued_copies = total_copies - available_copies
    overdue = [t for t in active if t["is_overdue"]]

    collected = sum(t["fine_amount"] for t in all_txns if t["status"] == "RETURNED")
    outstanding = sum(t["current_fine"] for t in overdue)

    return {
        "total_titles": len(books),
        "total_copies": total_copies,
        "available_copies": available_copies,
        "issued_copies": issued_copies,
        "active_loans": len(active),
        "overdue_count": len(overdue),
        "fines_collected": round(collected, 2),
        "fines_outstanding": round(outstanding, 2),
        "total_members": len(get_all_members()),
        "overdue_list": overdue,
        "categories": _category_breakdown(books),
    }


def _category_breakdown(books):
    breakdown = {}
    for b in books:
        breakdown[b["category"]] = breakdown.get(b["category"], 0) + 1
    return breakdown
