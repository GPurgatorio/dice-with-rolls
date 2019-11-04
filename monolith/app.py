from flask import Flask
from flask_cors import CORS
# from monolith.cache import cache
from monolith.database import db, User, Story, ReactionCatalogue
from monolith.views import blueprints
from monolith.auth import login_manager
import datetime


def create_app():
  
    flask_app = Flask(__name__)
    flask_app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    flask_app.config['SECRET_KEY'] = 'ANOTHER ONE'
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storytellers.db'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # cache config
    flask_app.config['CACHE_TYPE'] = 'simple'
    flask_app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    # cache.init_app(app)

    for bp in blueprints:
        flask_app.register_blueprint(bp)
        bp.app = flask_app

    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    db.create_all(app=flask_app)

    # create a first admin user
    with flask_app.app_context():
        q = db.session.query(User).filter(User.email == 'example@example.com')
        user = q.first()
        if user is None:
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            db.session.add(example)
            db.session.commit()

        q = db.session.query(Story).filter(Story.id == 1)
        story = q.first()
        if story is None:
            example = Story()
            example.text = 'Trial story of example admin user :)'
            example.author_id = 1
            example.figures = 'example#admin'
            example.date = datetime.datetime.strptime('2019-10-20', '%Y-%m-%d')
            print(example)
            db.session.add(example)
            db.session.commit()

        q = db.session.query(ReactionCatalogue)
        catalogue = q.all()
        if len(catalogue) == 0:
            like = ReactionCatalogue()
            like.reaction_id = 1
            like.reaction_caption = 'Like'
            dislike = ReactionCatalogue()
            dislike.reaction_id = 2
            dislike.reaction_caption = 'Dislike'
            db.session.add(like)
            db.session.add(dislike)
            db.session.commit()

    return flask_app


app = create_app()

if __name__ == '__main__':
    app.run()
