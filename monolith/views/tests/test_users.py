import datetime
import json
import random as rnd
import unittest

import flask_testing
from flask import Flask
from monolith.views import blueprints
from monolith.app import app as my_app
from monolith.database import Story, User, db
from monolith.urls import RANGE_URL, LATEST_URL
from monolith.auth import login_manager
from monolith.forms import LoginForm

from monolith.database import Story, User, db, Follower, ReactionCatalogue, Counter

class TestTemplateStories(flask_testing.TestCase):

    def create_app(self):
        global app
        app = Flask(__name__, template_folder='../../templates')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
        app.config['SECRET_KEY'] = 'ANOTHER ONE'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['WTF_CSRF_ENABLED'] = False

        app.config['LOGIN_DISABLED'] = True
        # cache config
        app.config['CACHE_TYPE'] = 'simple'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300

        for bp in blueprints:
            app.register_blueprint(bp)
            bp.app = app

        db.init_app(app)
        login_manager.init_app(app)
        db.create_all(app=app)

        return app

    # Set up database for testing here
    def setUp(self) -> None:
        print("SET UP")
        with app.app_context():
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            db.session.add(example)

            # Add some stories for user 1
            example = Story()
            example.text = 'Trial story of example admin user :)'
            example.author_id = 1
            example.figures = 'example#admin'
            db.session.add(example)
            db.session.commit()

            example = Story()
            example.text = 'Another story!'
            example.author_id = 1
            example.figures = 'another#story'
            db.session.add(example)
            db.session.commit()

            # Add some reactions
            like = ReactionCatalogue()
            like.reaction_id = 1
            like.reaction_caption = 'Like'
            dislike = ReactionCatalogue()
            dislike.reaction_id = 2
            dislike.reaction_caption = 'Dislike'
            db.session.add(like)
            db.session.add(dislike)
            db.session.commit()

            # Add reactions for story 1
            q = db.session.query(Counter)
            like = Counter()
            like.reaction_type_id = 1
            like.story_id = 1
            like.counter = 23
            dislike = Counter()
            dislike.reaction_type_id = 2
            dislike.story_id = 1
            dislike.counter = 5
            db.session.add(like)
            db.session.add(dislike)
            db.session.commit()

            payload = {'email': 'example@example.com',
                   'password': 'admin'}

            form = LoginForm(data=payload)

            self.client.post('/users/login', data=form.data, follow_redirects=True)

     # Executed at end of each test
    def tearDown(self) -> None:
        print("TEAR DOWN")
        db.session.remove()
        db.drop_all()

    # TO fix
    # def test_user_statistics(self):
    #     response = self.client.get('/users/1')
    #     self.assert_template_used('wall.html')
    #     test_user = User.query.filter_by(id=1)
    #     #self.assertEqual(self.get_context_variable('user_info'), test_user)
    #     test_stats = [('num_reactions', 28), ('num_stories', 2)]
    #     self.assertEqual(self.get_context_variable('stats'), test_stats)
