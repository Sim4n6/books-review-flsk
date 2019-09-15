# std lib
import csv
import os

# third party modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine("postgres://muylahjtlgacxa:17a9ecdf9048d7689884cbba513c6edee10bc31495dd16a714793d4b75a54ac1@ec2-23-21-156-171.compute-1.amazonaws.com:5432/d9u182t2pj14oq", echo=True)
db = scoped_session(sessionmaker(bind=engine))


if __name__ == "__main__":

    # Create all 
    db.execute("CREATE TABLE authors (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL);")
    db.execute("CREATE TABLE books (id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, title VARCHAR NOT NULL, year INTEGER NOT NULL, author_id INTEGER REFERENCES authors );")

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