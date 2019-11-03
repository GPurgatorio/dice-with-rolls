import datetime

from flask import Flask

from monolith.auth import login_manager
from monolith.database import db, User, Story, ReactionCatalogue
from monolith.views import blueprints


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

        q = db.session.query(User).filter(User.email == 'abc@abc.com')
        user = q.first()
        if user is None:
            example = User()
            example.firstname = 'Abc'
            example.lastname = 'Abc'
            example.email = 'abc@abc.com'
            example.dateofbirth = datetime.datetime(2010, 10, 5)
            example.is_admin = False
            example.set_password('abc')
            db.session.add(example)
            db.session.commit()

        q = db.session.query(User).filter(User.email == 'nini@nini.com')
        user = q.first()
        if user is None:
            example = User()
            example.firstname = 'Nini'
            example.lastname = 'Nini'
            example.email = 'nini@nini.com'
            example.dateofbirth = datetime.datetime(2010, 10, 7)
            example.is_admin = False
            example.set_password('nini')
            db.session.add(example)
            db.session.commit()

        # no stories
        q = db.session.query(User).filter(User.email == 'no@stories.com')
        user = q.first()
        if user is None:
            example = User()
            example.firstname = 'No'
            example.lastname = 'Stories'
            example.email = 'no@stories.com'
            example.dateofbirth = datetime.datetime(2010, 10, 5)
            example.is_admin = False
            example.set_password('no')
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
            db.session.add(example)
            db.session.commit()

        q = db.session.query(Story).filter(Story.id == 2)
        story = q.first()
        if story is None:
            example = Story()
            example.text = 'Old story (dont see this in /latest)'
            example.date = datetime.datetime.strptime('2019-10-10', '%Y-%m-%d')
            example.likes = 420
            example.author_id = 2
            example.figures = 'example#abc'
            db.session.add(example)
            db.session.commit()

        q = db.session.query(Story).filter(Story.id == 3)
        story = q.first()
        if story is None:
            example = Story()
            example.text = 'You should see this one in /latest'
            example.date = datetime.datetime.strptime('2019-10-13', '%Y-%m-%d')
            example.likes = 3
            example.author_id = 2
            example.figures = 'example#abc'
            db.session.add(example)
            db.session.commit()

        q = db.session.query(Story).filter(Story.id == 4)
        story = q.first()
        if story is None:
            example = Story()
            example.text = 'story from not admin'
            example.date = datetime.datetime.strptime('2018-12-30', '%Y-%m-%d')
            example.likes = 100
            example.author_id = 3
            example.figures = 'example#nini'
            db.session.add(example)
            db.session.commit()

        q = db.session.query(Story).filter(Story.id == 5)
        story = q.first()
        if story is None:
            example = Story()
            example.text = 'very old story (11 11 2011)'
            example.date = datetime.datetime.strptime('2011-11-11', '%Y-%m-%d')
            example.likes = 2
            example.author_id = 3
            example.figures = 'example#nini'
            example.date = datetime.datetime(2011, 11, 11)
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
