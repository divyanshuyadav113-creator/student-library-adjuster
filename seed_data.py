"""
seed_data.py
Optional helper that populates the library with sample books, members,
and a couple of loans (including one overdue one) so the dashboard has
something to show right after cloning the repo. Handy for demo
screenshots on your resume/portfolio.

Run with:
    python seed_data.py
"""

from datetime import date, timedelta

from database import init_db, get_cursor
import models
from qr_utils import generate_book_qr

SAMPLE_BOOKS = [
    ("978-0132350884", "Clean Code", "Robert C. Martin", "Software", 2),
    ("978-0451524935", "1984", "George Orwell", "Fiction", 1),
    ("978-0060850524", "Brave New World", "Aldous Huxley", "Fiction", 2),
    ("978-0596007126", "Head First Design Patterns", "Eric Freeman", "Software", 1),
    ("978-0307474278", "The Da Vinci Code", "Dan Brown", "Thriller", 3),
    ("978-0141439518", "Pride and Prejudice", "Jane Austen", "Classics", 2),
]

SAMPLE_MEMBERS = [
    ("Alice Sharma", "alice@example.com", "555-0101"),
    ("Bob Kumar", "bob@example.com", "555-0102"),
    ("Priya Nair", "priya@example.com", "555-0103"),
]


def run():
    init_db()

    book_ids = []
    for isbn, title, author, category, copies in SAMPLE_BOOKS:
        bid = models.add_book(isbn, title, author, category, copies)
        qr_path = generate_book_qr(bid, isbn, title)
        models.set_book_qr(bid, qr_path)
        book_ids.append(bid)

    member_ids = []
    for name, email, phone in SAMPLE_MEMBERS:
        mid = models.add_member(name, email, phone)
        member_ids.append(mid)

    # A normal, on-time loan
    models.issue_book(book_ids[0], member_ids[0])

    # An overdue loan -- backdate it manually so the dashboard shows a fine
    with get_cursor(commit=True) as cur:
        overdue_issue = date.today() - timedelta(days=20)
        overdue_due = date.today() - timedelta(days=6)
        cur.execute(
            """INSERT INTO transactions (book_id, member_id, issue_date, due_date, status)
               VALUES (?, ?, ?, ?, 'ISSUED')""",
            (book_ids[1], member_ids[1], overdue_issue.isoformat(), overdue_due.isoformat()),
        )
        cur.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
            (book_ids[1],),
        )

    print("Sample data loaded: 6 books, 3 members, 2 active loans (1 overdue).")
    print("Run `python app.py` and open http://127.0.0.1:5000")


if __name__ == "__main__":
    run()
