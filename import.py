# std lib
import csv
import os

# third party modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
db = scoped_session(sessionmaker(bind=engine))


if __name__ == "__main__":

    # Create all 
    db.execute("CREATE TABLE authors (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL);")
    db.execute("CREATE TABLE books (id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, title VARCHAR NOT NULL, year INTEGER NOT NULL, author_id INTEGER REFERENCES authors );")
    db.execute("CREATE TABLE reviews (id SERIAL PRIMARY KEY, note SMALLINT DEFAULT 5, book_id INTEGER REFERENCES books); ")
    # users table for login/registration.    
    db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR NOT NULL, password VARCHAR NOT NULL); ")
    
    # read csv file content
    f = open("books.csv")
    reader = csv.reader(f)
    reader.__next__() # avoid fieldnames
    for isbn, title, author, year in reader:
        # check author not in DB, if not insert it           
        if db.execute("SELECT * FROM authors WHERE name = :name", { "name":author }).fetchone() is None:
            db.execute("INSERT INTO authors(name) VALUES(:name)", {"name":author})  
    db.commit()

    f.seek(0)
    reader.__next__()
    for isbn, title, author, year in reader:
        # check book not in DB
        if db.execute("SELECT * FROM books WHERE title = :title", { "title":title }).fetchone() is None:
            # retrieve id of author of the book
            author_found = db.execute("SELECT * FROM authors WHERE name = :name", { "name":author }).fetchone()
            # insert book into db
            db.execute("INSERT INTO books(isbn, title, year, author_id) VALUES( :isbn, :title, :year, :author_id)", { "isbn":isbn, "title":title, "year":int(year), "author_id":author_found.id })
    db.commit()
    f.close()