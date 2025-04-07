from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from forms import RegistrationForm, LoginForm, PostForm
from models import User, Post
from config import Config
from flask import g
import functools

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)  #Enable CSRF protection.  VERY IMPORTANT in real projects

# In a real application, you'd use a proper session management system.
# This is a simple in-memory dictionary for demonstration purposes only.
users = {}  # Store user credentials (username: password)  NEVER DO THIS IN REAL LIFE
logged_in_user = None


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))

        return view(**kwargs)

    return wrapped_view


@app.before_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    global logged_in_user  #Access the global variable
    if logged_in_user: #If a user is "logged in" (very basic implementation)
        g.user = User.query.filter_by(username=logged_in_user).first()
    else:
        g.user = None


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index')) #redirect to prevent resubmission on refresh

    #posts = Post.query.order_by(Post.timestamp.desc()).all() #All posts
    posts = g.user.followed_posts().all()  #Only followed and own posts
    return render_template('index.html', title='Home', form=form, posts=posts)


@app.route('/register', methods=('GET', 'POST'))
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        #VERY IMPORTANT: NEVER store passwords in plaintext. Use a proper hashing algorithm (bcrypt, scrypt, argon2)
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
