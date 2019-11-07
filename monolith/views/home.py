from flask import Blueprint, render_template

from flask_login import current_user
from monolith.database import db, Story
from monolith.urls import LOGIN_URL, LOGOUT_URL, USERS_URL, READ_URL, REGISTER_URL, SETTINGS_URL, SEARCH_URL

home = Blueprint('home', __name__)


@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        stories = db.session.query(Story).filter(Story.author_id == current_user.id)
    else:
        stories = None
    context_vars = {"stories": stories, "register_url": REGISTER_URL,
                    "login_url": LOGIN_URL, "logout_url": LOGOUT_URL,
                    "read_url": READ_URL, "settings_url": SETTINGS_URL,
                    "search_url": SEARCH_URL,
                    "users_url": USERS_URL}
    return render_template("index.html", **context_vars)
