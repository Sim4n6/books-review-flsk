import os
import decimal

import requests
import bcrypt 

from flask import Flask, session, render_template, request, url_for, jsonify, redirect, flash
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
    if session.get("email") is None:
        return render_template("index.html", logged_out=True)
    
    if session.get("email") is not None:
        return render_template("index.html", logged_out=False)


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        user_found = db.execute("SELECT * FROM users WHERE users.email = :email", {"email":email}).fetchone()
        if user_found is None:
            db.execute("INSERT INTO users (email, password) VALUES (:email, :password)", {"email":email, "password": hashed.decode("utf-8")})
            db.commit()
            flash("Registration done with success. Please login with your credentials.")
        else:
            flash(f"An account is already there with the email : {email}")
        return redirect(url_for("index")) 

    return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        password_retrieved = db.execute("SELECT password FROM users WHERE users.email = :email", {"email":email}).fetchone()
        hashed = password_retrieved[0].encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), hashed):
            flash("Password Matches!")
            # redirect to protected after storing in session
            session["email"] = email
            return redirect(url_for("index"))
        else:
            flash("It Does not Match :(")
        #return redirect(url_for("index")) 

    return render_template("login.html")


@app.route("/logout")
def logout():
    if session.get('email') is not None:
        session.pop('email')
        flash("You are now logged out.")
    return redirect(url_for("index"))

@app.route("/search", methods=["POST", "GET"])
def search():
    if session.get("email") is not None:
        data = dict()
        books_by_isbn = None 
        books_by_title = None 
        books_by_author = None 
        if request.method == "POST":
            # retrieve of submitted data to the form
            data["isbn"] = request.form['isbn']
            data["title"] = request.form['title']
            data["author"] = request.form['author']
            
            # searching by isbn      
            if data["isbn"] != "":
                tag = f"%{data['isbn']}%"
                books_by_isbn = db.execute("""SELECT * FROM books JOIN authors ON books.author_id = authors.id WHERE books.isbn LIKE :isbn ;""", {"isbn": tag})

            # search by title 
            if data["title"] != "" :
                tag = f"%{data['title']}%"
                books_by_title = db.execute("""SELECT * FROM books JOIN authors ON books.author_id = authors.id WHERE books.title ILIKE :title ;""", {"title": tag})

            # search by author 
            if data["author"] != "":
                tag = f"%{data['author']}%"
                books_by_author = db.execute("""SELECT * FROM books JOIN authors ON books.author_id = authors.id WHERE authors.name ILIKE :author ;""", {"author": tag})
            
        return render_template("search.html",  books_by_isbn=books_by_isbn, books_by_title=books_by_title, books_by_author=books_by_author)
    else:
        return redirect(url_for("index"))


@app.route("/book", methods=["GET"])
def no_book():
    return redirect(url_for("index"))
    

@app.route("/book/<int:bid>", methods=["GET", "POST"])
def book(bid=None):
    if session.get("email") is not None:
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
    else:
        return redirect(url_for("index", logged_out=True))


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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message = "Error 404 : page not found."), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('error.html', message = "Eroor 500 : Server side error."), 500


if __name__ == "__main__":
    app.run(load_dotenv=True)
