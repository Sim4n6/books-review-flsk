import os

from flask import Flask, session, render_template, request, url_for
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
engine = create_engine(os.getenv("DATABASE_URL"))
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
    return render_template("search_form.html", data=data)


@app.route("/book", methods=["GET"])
@app.route("/book/<int:bid>", methods=["GET"])
def book(bid=None):
    if bid is None: 
        return render_template("error.html", message="Please, provide a book id.")
        
    book_w_author = db.execute("SELECT * FROM books JOIN authors ON books.author_id = authors.id WHERE books.id = :bid ", {"bid":bid}).fetchone()
    if book_w_author is None:
        return render_template("error.html", message="The book id is not correct.")

    return render_template("book.html", book = book_w_author)

if __name__ == "__main__":
    app.run(load_dotenv=True)
