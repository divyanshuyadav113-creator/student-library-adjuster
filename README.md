# Stackroom — Mini Library Management System

A small library management system built with **Python (Flask)** and
**SQLite**, featuring QR codes for books, an automatic fine calculator,
live book availability tracking, and a dashboard.

Built as a portfolio project — clean architecture (data layer / business
logic / routes kept in separate files), no ORM magic, easy to read in
one sitting.

## Features

- **Book catalog** — add, search, and remove books; each title tracks
  total vs. available copies in real time.
- **QR codes** — every book automatically gets a QR code (generated with
  the `qrcode` library) encoding its ID, ISBN, and title. Print it for
  the shelf or cover; scanning it with any phone reveals the book's
  details instantly.
- **Circulation** — issue a book to a member (14-day loan) and return
  it later; available copies update automatically and can't go negative.
- **Fine calculator** — configurable per-day overdue rate with a cap,
  used automatically on return and also available as a standalone tool
  to calculate a fine for any due/return date pair.
- **Dashboard** — live counts of titles, copies available, active
  loans, overdue books, fines collected vs. outstanding, and a
  category breakdown.
- **Member registry** and a full **transaction ledger** with fine
  payment tracking.

## Tech stack

- Python 3 / Flask
- SQLite (plain `sqlite3`, no ORM — easy to read and extend)
- `qrcode` + `Pillow` for QR generation
- Jinja2 templates, hand-written CSS (no frontend framework/build step)

## Project structure

```
library-management-system/
├── app.py             # Flask routes
├── models.py           # data-access layer (books, members, transactions)
├── database.py         # SQLite connection + schema
├── fines.py            # fine calculation rules
├── qr_utils.py         # QR code generation
├── seed_data.py         # optional: loads sample data for a quick demo
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── qrcodes/         # generated QR images land here
└── templates/           # Jinja2 HTML templates
```

## Getting started

```bash
# 1. Clone the repo
git clone https://github.com/Utsavpanchal0810/library-management-system.git
cd library-management-system

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) load sample data so the dashboard isn't empty
python seed_data.py

# 5. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

Running `app.py` also creates `library.db` automatically the first
time, so step 4 is optional — you can start from a completely empty
catalog if you'd rather add your own books.

## How the fine calculator works

Policy lives in one place, `fines.py`, so it's easy to tune:

```python
LOAN_PERIOD_DAYS = 14   # loan length
GRACE_PERIOD_DAYS = 0   # days of grace before fines start
FINE_PER_DAY = 5.0      # charged per day overdue
MAX_FINE = 200.0        # fine is capped
```

`calculate_fine(due_date, return_date)` is used in two places: silently
when a book is returned (to log the fine on the transaction), and in
the standalone **Fine Calculator** page, which lets you check what the
fine would be for any due date / return date combination.

## How the QR codes work

When a book is added, `qr_utils.generate_book_qr()` encodes a small
JSON payload — `{book_id, isbn, title}` — into a PNG saved under
`static/qrcodes/`. The image is shown on the book's "View QR" page and
can be printed and stuck on the shelf or inside the cover; any generic
QR scanner app can read it back for a fast lookup.

## Possible next steps

- Barcode/QR *scanning* (via a webcam) to issue/return books instead of
  picking from a dropdown
- Email/SMS reminders before a book becomes overdue
- Multi-user login (librarian vs. member roles)
- Export the ledger to CSV/PDF

## License

MIT — free to use for learning, portfolios, or as a starting point for
something bigger.
