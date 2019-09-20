# Project 1

Web Programming with Python and JavaScript

The web app for the **project1** could be tested online on heroku at <https://books-review-flsk.herokuapp.com>


# Files description : 

1. static/favicon.png : a favicon icone for the beautiful website.
1. templates/auth/ login.html and register.html : templates for login and registration.
1. templates/book.html : template for book detail.
1. templates/error.html: a simple yet a personnalized error template for 404 and 500 errors.
1. templates/index.html: index template.
1. templates/layout.html : a basic layout from where all templates inherits and it contains jumbotron and include a menu.html (nav).
1. templates/search.html : multicriteria search template.

1. .gitignore : a git ignore list of files including .env for env variables and flask sessions.
1. application.py : main file that contains the whole flask app (backend)
1. books.csv last line was removed since it is an empty one.
1. import.py read csv file content twice and create the db SCHEMA.
1. Pipfile and Pipfile.lock files dedicated for pipenv a virtual environment management.
1. Procfile : heroku platform config file.
1. requirements.txt : a freezed version of the pipfile.
1. subtitles.srt : for the video on youtube.

# API access : 

--> <https://books-review-flsk.herokuapp.com/api/1632168146> replace 1632168146 with any isbn please. 
