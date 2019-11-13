from flask import Blueprint, render_template

from flask_login import current_user
from monolith.database import db, Story
from monolith.urls import HOME_URL

home = Blueprint('home', __name__)


@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        stories = db.session.query(Story).filter(Story.author_id == current_user.id)
    else:
        stories = None
    context_vars = {"stories": stories, "home_url": HOME_URL}
    return render_template("index.html", **context_vars)
