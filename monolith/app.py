import os
from flask import Flask
# from monolith.cache import cache
from monolith.database import db, User, Story, ReactionCatalogue
from monolith.views import blueprints
from monolith.auth import login_manager
from monolith.tasks import task_try
import datetime


def create_app():
    app = Flask(__name__)
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storytellers.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # cache config
    app.config['CACHE_TYPE'] = 'simple'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    # cache.init_app(app)

    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    db.init_app(app)
    login_manager.init_app(app)
    db.create_all(app=app)

    # create a first admin user
    with app.app_context():
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
            print(example)
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
            print(example)
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
            print(example)
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
            print(example)
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

    return app


app = create_app()

if __name__ == '__main__':
    task_try.delay()
    app.run()
