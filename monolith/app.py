from flask import Flask

from monolith.auth import login_manager
from monolith.database import db, ReactionCatalogue
from monolith.urls import DEFAULT_DB
from monolith.views import blueprints


def create_app(database=DEFAULT_DB, wtf=False, login_disabled=False):
    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    flask_app.config['SECRET_KEY'] = 'ANOTHER ONE'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = database
    flask_app.config['WTF_CSRF_ENABLED'] = wtf
    flask_app.config['LOGIN_DISABLED'] = login_disabled

    for bp in blueprints:
        flask_app.register_blueprint(bp)
        bp.app = flask_app

    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    db.create_all(app=flask_app)

    with flask_app.app_context():
        # Possible reactions
        if ReactionCatalogue.query.filter(ReactionCatalogue.reaction_caption == 'like').first() is None:
            like = ReactionCatalogue()
            like.reaction_id = 1
            like.reaction_caption = 'like'
            db.session.add(like)
            db.session.commit()

        if ReactionCatalogue.query.filter(ReactionCatalogue.reaction_caption == 'dislike').first() is None:
            dislike = ReactionCatalogue()
            dislike.reaction_id = 2
            dislike.reaction_caption = 'dislike'
            db.session.add(dislike)
            db.session.commit()

    return flask_app


app = create_app()
