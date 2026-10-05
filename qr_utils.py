"""
qr_utils.py
Generates a QR code image for a book. The QR code encodes a small JSON
payload (id + ISBN + title) so any phone QR scanner can identify the
book instantly at the shelf, and it doubles as a fast lookup key for a
future barcode-scanner-style "issue book" flow.
"""

import json
import os

import qrcode

QR_FOLDER = os.path.join("static", "qrcodes")


def _ensure_folder():
    os.makedirs(QR_FOLDER, exist_ok=True)


def generate_book_qr(book_id: int, isbn: str, title: str) -> str:
    """Creates static/qrcodes/book_<id>.png and returns its relative path
    (relative to the static/ folder, ready to use in url_for('static', ...))."""
    _ensure_folder()

    payload = json.dumps({"book_id": book_id, "isbn": isbn, "title": title})

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"book_{book_id}.png"
    filepath = os.path.join(QR_FOLDER, filename)
    img.save(filepath)

    return f"qrcodes/{filename}"


def delete_book_qr(qr_path: str):
    """Removes a QR image when a book is deleted, if it exists."""
    if not qr_path:
        return
    full_path = os.path.join("static", qr_path)
    if os.path.exists(full_path):
        os.remove(full_path)
