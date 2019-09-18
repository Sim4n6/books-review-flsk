import os
import decimal

import requests
from flask import Flask, session, render_template, request, url_for, jsonify, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Project 1: TODO"


@app.route("/search", methods=["POST", "GET"])
def search():
    data = dict()
    if request.method == "POST":
        data["isbn"] = request.form['isbn']
        data["title"] = request.form['title']
        data["author"] = request.form['author']
    return render_template("search.html", data=data)


@app.route("/book", methods=["GET"])
def no_book():
    return redirect(url_for("index"))
    

@app.route("/book/<int:bid>", methods=["GET", "POST"])
def book(bid=None):
    if bid is None and request.method != "POST": 
        return render_template("error.html", message="Please, provide a book id.")

    if request.method == "POST":
        review = request.form["review"]
        review_of_book = db.execute("SELECT * FROM reviews JOIN books ON reviews.book_id = books.id WHERE books.id = :bid", {"bid":bid}).fetchone()
        if review_of_book is None:
            db.execute("INSERT INTO reviews (note, book_id) VALUES (:review, :bid)", {"review":review, "bid":bid})
            db.commit()
        else:
            db.execute("UPDATE reviews SET note = :review WHERE reviews.book_id = :bid;", {"review":review, "bid":bid})
            db.commit()

    book_w_author = db.execute("SELECT * FROM books JOIN authors ON books.author_id = authors.id WHERE books.id = :bid ", {"bid":bid}).fetchone()
    if book_w_author is None:
        return render_template("error.html", message="The book id is not correct.")

    # retrieve of Goodreads stats
    res = requests.get("https://www.goodreads.com/book/review_counts.json", { "key": "MvlTUAcubLq9uNaWxUXYtg", "isbns":book_w_author.isbn})
    d = res.json()
    goodreads = dict()
    goodreads["avg"] = d.get("books")[0].get("average_rating")
    goodreads["total"] = d.get("books")[0].get("work_ratings_count")

    # 
    review_previous_note = db.execute("SELECT note FROM reviews WHERE reviews.book_id = :book_id;", {"book_id":bid}).fetchone()
    if review_previous_note is None:
        return render_template("book.html", book=book_w_author, bid=bid, goodreads=goodreads, review_previous_note=5)    # default selected option is 5

    return render_template("book.html", book=book_w_author, bid=bid, goodreads=goodreads, review_previous_note=review_previous_note[0])


@app.route("/api", methods=["GET"])
@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn=None):
    if isbn is None:
        return render_template("error.html", message="Please provide an ISBN with /api route."), 404

    book = db.execute("SELECT * FROM books WHERE isbn = :isbn ;", {"isbn":isbn}).fetchone()
    if book is None:
        return render_template("error.html", message="ISBN is not valid."), 404

    res = dict()
    res["title"] = book.title
    res["year"] = book.year
    res["isbn"] = book.isbn
    author = db.execute("SELECT * FROM authors WHERE authors.id = :author_id ;", {"author_id": book.author_id}).fetchone()
    res["author"] = author.name
    review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE reviews.book_id = :book_id ;", {"book_id": book.id}).fetchone()
    res["review_count"] = review_count[0]
    avg_score = db.execute("SELECT AVG(note) FROM reviews WHERE reviews.book_id = :book_id ;", {"book_id": book.id}).fetchone()
    if avg_score[0] is None :
        res["average_score"] = 0
    else:
        res["average_score"] = float(avg_score[0])

    return jsonify(res)


if __name__ == "__main__":
    app.run(load_dotenv=True)
