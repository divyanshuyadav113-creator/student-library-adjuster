"""
app.py
Flask entry point for the Mini Library Management System.
Run with:
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""
from flask import Flask, render_template, request, redirect, url_for, flash
import models
from database import init_db
from fines import fine_breakdown
from qr_utils import generate_book_qr, delete_book_qr
app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"
@app.route("/")
def dashboard():
    stats = models.get_dashboard_stats()
    return render_template("dashboard.html", stats=stats)
@app.route("/books")
def books():
    search = request.args.get("q", "").strip()
    all_books = models.get_all_books(search=search or None)
    return render_template("books.html", books=all_books, search=search)
@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        isbn = request.form["isbn"].strip()
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        category = request.form.get("category", "General").strip() or "General"
        copies = int(request.form.get("total_copies", 1))
        try:
            book_id = models.add_book(isbn, title, author, category, copies)
        except Exception as e:
            flash(f"Could not add book: {e}", "error")
            return redirect(url_for("add_book"))
        qr_path = generate_book_qr(book_id, isbn, title)
        models.set_book_qr(book_id, qr_path)
        flash(f'"{title}" added with a QR code generated.', "success")
        return redirect(url_for("books"))
    return render_template("add_book.html")
@app.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    book = models.get_book(book_id)
    if book:
        delete_book_qr(book.get("qr_path"))
        models.delete_book(book_id)
        flash(f'"{book["title"]}" removed.', "success")
    return redirect(url_for("books"))
@app.route("/books/<int:book_id>/qr")
def view_qr(book_id):
    book = models.get_book(book_id)
    if not book:
        flash("Book not found.", "error")
        return redirect(url_for("books"))
    return render_template("book_qr.html", book=book)
@app.route("/members")
def members():
    return render_template("members.html", members=models.get_all_members())
@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form.get("phone", "").strip()
        try:
            models.add_member(name, email, phone)
            flash(f"Member {name} added.", "success")
        except Exception as e:
            flash(f"Could not add member: {e}", "error")
            return redirect(url_for("add_member"))
        return redirect(url_for("members"))
    return render_template("add_member.html")
@app.route("/issue", methods=["GET", "POST"])
def issue():
    if request.method == "POST":
        book_id = int(request.form["book_id"])
        member_id = int(request.form["member_id"])
        success, message = models.issue_book(book_id, member_id)
        flash(message, "success" if success else "error")
        return redirect(url_for("issue"))
    return render_template(
        "issue_book.html",
        books=[b for b in models.get_all_books() if b["available_copies"] > 0],
        members=models.get_all_members(),
    )
@app.route("/return", methods=["GET", "POST"])
def return_book_view():
    if request.method == "POST":
        transaction_id = int(request.form["transaction_id"])
        success, message, fine = models.return_book(transaction_id)
        flash(message, "success" if success else "error")
        return redirect(url_for("return_book_view"))
    return render_template("return_book.html", active=models.get_active_transactions())
@app.route("/fines/<int:transaction_id>/pay", methods=["POST"])
def pay_fine(transaction_id):
    models.mark_fine_paid(transaction_id)
    flash("Fine marked as paid.", "success")
    return redirect(url_for("history"))
@app.route("/fine-calculator", methods=["GET", "POST"])
def fine_calculator():
    result = None
    if request.method == "POST":
        due_date = request.form["due_date"]
        return_date = request.form.get("return_date") or None
        result = fine_breakdown(due_date, return_date)
    return render_template("fine_calculator.html", result=result)
@app.route("/history")
def history():
    return render_template("history.html", transactions=models.get_all_transactions())
if __name__ == "__main__":
    init_db()
    app.run(debug=True)