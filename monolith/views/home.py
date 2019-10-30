from flask import Blueprint, render_template

from monolith.database import db, Story
from monolith.auth import current_user
from monolith.urls import HOME_URL, LOGIN_URL, LOGOUT_URL, READ_URL, REGISTER_URL, WRITE_URL, SETTINGS_URL

home = Blueprint('home', __name__)


def _strava_auth_url(config):
    return '127.0.0.1:5000'


@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        stories = db.session.query(Story).filter(Story.author_id == current_user.id)
    else:
        stories = None
    context_vars = {"stories": stories, "register_url": REGISTER_URL,
                    "login_url": LOGIN_URL, "logout_url": LOGOUT_URL,
                    "read_url": READ_URL, "settings_url": SETTINGS_URL}
    return render_template("index.html", **context_vars)
