from flask import Blueprint, render_template, request
from sqlalchemy import or_

from monolith.database import Story, User
from monolith.urls import USERS_URL, READ_URL, SEARCH_URL, REACTION_URL

search = Blueprint('search', __name__)


@search.route('/search')
def _search():
    list_of_users = list_of_stories = []
    query = request.args.get('query')
    if query is not None:
    	query = query.strip()
    	list_of_users, list_of_stories = _search_query(query)

    context_vars = {"list_of_stories": list_of_stories, "list_of_users": list_of_users,
                    "reaction_url": REACTION_URL, "search_url": SEARCH_URL,
                    "users_url": USERS_URL, "story_url": READ_URL}
    return render_template("search.html", **context_vars)


def _search_query(query):
	list_of_users = list_of_stories = []
	if query.strip() != '':
		list_of_users = User.query.filter(
			or_(User.firstname.like('%' + query + '%'), User.lastname.like('%' + query + '%'))).all()
		list_of_stories = Story.query.filter(Story.figures.like('%#' + query + '#%')).all()
	return list_of_users, list_of_stories
