from flask import Blueprint, render_template
from sqlalchemy import or_

from monolith.database import db, Story, Reaction, User
from monolith.auth import current_user
from monolith.urls import HOME_URL, LOGIN_URL, LOGOUT_URL, USERS_URL, READ_URL, REGISTER_URL, WRITE_URL, SEARCH_URL

search = Blueprint('search', __name__)


@search.route('/search')
def _search(list_of_stories=[], list_of_users=[], message=''):
    context_vars = {"list_of_stories": list_of_stories, "list_of_users": list_of_users,
                    "login_url": LOGIN_URL, "logout_url": LOGOUT_URL,
                    "read_url": READ_URL, "search_url": SEARCH_URL,
                    "users_url": USERS_URL, "message": message}
    return render_template("search.html", **context_vars)


@search.route('/search/query/<query>')
def _search_query(query):
    list_of_stories = Story.query.filter(Story.figures.like('%#' + query + '#%')).all()
    list_of_users = User.query.filter(or_(User.firstname.like('%' + query + '%'), User.lastname.like('%' + query + '%'))).all()

    return _search(list_of_stories=list_of_stories, list_of_users=list_of_users)
