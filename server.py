"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")

@app.route('/users')
def user_list():
    """Show list of users."""

    # get all User instances from users table in database
    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route('/users/<userid>')
def users_info(userid):
    """Show individual user page"""

    # queries database for user_id, age, zipcode for given user id
    user = (db.session.query(User.user_id, User.age, User.zipcode)
                     .filter(User.user_id == userid).one())

    # queries database for score and movie title for all user's rankings
    user_movie_ratings =  (db.session.query(User.user_id, 
                                            Rating.score, 
                                            Movie.title)
                           .join(Rating)
                           .join(Movie)
                           .filter(User.user_id == userid)
                           .all())

    # goes to individual user page, passing in user and rating info
    return render_template("users.html", 
                           user=user, 
                           user_movie_ratings=user_movie_ratings)

@app.route('/movies')
def movie_list():
    """Show list of movies."""

    # get all Movie instances from movies table in database
    movies = Movie.query.order_by("title").all()
    return render_template("movies_list.html", movies=movies)

@app.route('/movies/<movieid>')
def movie_info(movieid):
    """Show individual movie page"""

    # queries database for movie instance that matches movie id
    movie = Movie.query.filter(Movie.movie_id == movieid).one()

    # queries database for score and movie title for all user's rankings
    movie_ratings =  (db.session.query(Movie.movie_id, 
                                            Rating.score, 
                                            User.email)
                           .join(Rating)
                           .join(User)
                           .filter(Movie.movie_id == movieid)
                           .all())

    # goes to individual movie page, passing in movie and rating info
    return render_template("movie.html", 
                           movie=movie, 
                           movie_ratings=movie_ratings)

@app.route('/movies/<movieid>', methods=["POST"])
def rate_info(movieid):
    """Add or update movie rating for logged in user"""

    # gets provided score from movie.html HTML form
    score = request.form.get("score")

    # query database to see if user has already rated this movie (rating exists)
    rating = Rating.query.filter(Rating.movie_id == movieid, 
                                 Rating.user_id == session['userid']).first()

    # if rating exists:
    if rating:
        # update score in rating instance
        rating.score = score
        flash("Your updated rating was recorded.")
    # if rating doesn't exist:
    else:
        # create new instance of Rating class
        new_rating = Rating(user_id=session['userid'], 
                            movie_id=movieid, 
                            score=score)
        # add new rating to database
        db.session.add(new_rating)
        flash("Your new rating was recorded.")

    # commit changes to database
    db.session.commit()

    return redirect('/movies')

@app.route('/register', methods=["GET"])
def register_form():
    """Show registration form"""

    return render_template("register_form.html")

@app.route('/register', methods=["POST"])
def register_process():
    """Process user registration"""

    # take user input from register_form.html
    email = request.form.get("email")
    password = request.form.get("password")

    # query users table in database, retrieve user instance that matches email    
    user = User.query.filter(User.email == email).first()

    # if there is a user in database that matches email    
    if user:
        flash("Account already exists. Please login.")
        return redirect("/login")

    # if email is not already in database, create new instance of User class
    new_user = User(email=email, password=password)
    # add new user instance to users table in database
    db.session.add(new_user)
    db.session.commit()

    flash("User account created. Please login.")
    return redirect("/login")

@app.route('/login', methods=["GET"])
def login_form():
    """Show login form"""

    # Check browser session to see if user already logged in
    if session.get('userid'):
        flash("Already logged in.")

        # redirect to logged in user's page 
        # using string formatting to pass in user id from session (cookie-ish)
        return redirect("/users/{}".format(session['userid']))

    # if not logged in, render login form
    return render_template("login_form.html")

@app.route('/login', methods=["POST"])
def login_process():
    """Process user login"""

    # take user input from login_form.html
    email = request.form.get("email")
    password = request.form.get("password")

    # query users table in database, retrieve user instance that matches email
    user = User.query.filter(User.email == email).first()

    # if there is a user in database that matches email
    if user:
        # if input password matches:
        if password == user.password:
            session['userid'] = user.user_id
            flash("Logged In")

        # redirect to logged in user's page 
        # using string formatting to pass in user id from session (cookie-ish)
        return redirect("/users/{}".format(session['userid']))

    # if user not in database or password incorrect
    flash("Login Failed")
    return redirect("/login")

@app.route('/logout')
def logout():
    """Process user logout"""

    # if browser session exists (logged in), then logout
    if session.get('userid'):    
        session.pop("userid")
        flash("Logged out.")
    
    return redirect("/")





if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
