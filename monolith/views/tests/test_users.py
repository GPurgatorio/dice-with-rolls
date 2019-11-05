import datetime
import json
import random as rnd
import unittest

import flask_testing
from flask import Flask
from monolith.app import app as my_app
from monolith.views import blueprints
from monolith.forms import LoginForm, UserForm
from monolith.auth import login_manager
from monolith.database import Story, User, db
from monolith.urls import RANGE_URL, LATEST_URL

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
            # Add Admin user
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            db.session.add(example)

            # Add another user for testing
            example = User()
            example.firstname = 'Test'
            example.lastname = 'Man'
            example.email = 'test@test.com'
            example.dateofbirth = datetime.datetime(2020, 10, 6)
            example.is_admin = False
            example.set_password('test')
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

            # Add reactions for user 1
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
        
    def test_user_statistics(self):
        self.client.get('/users/1')
        self.assert_template_used('wall.html')
        # I should be logged as admin so i'm looking for my wall
        self.assertEqual(self.get_context_variable('my_wall'), True)
        num_stories = Story.query.filter_by(author_id=1).count()
        self.assertEqual(self.get_context_variable('stats')[2][1], num_stories)
        reactions = 28 # 23 Likes + 5 Dislikes
        self.assertEqual(self.get_context_variable('stats')[1][1], reactions)
        avg_dice = 2.0 # every story has 2 figures
        self.assertEqual(self.get_context_variable('stats')[3][1], avg_dice)
        avg_reactions = 14
        self.assertEqual(self.get_context_variable('stats')[0][1], avg_reactions)

    def test_someone_statistics(self):
        self.client.get('/users/2')
        self.assert_template_used('wall.html')
        # I should be logged as admin and looking for someone's wall
        self.assertEqual(self.get_context_variable('my_wall'), False)
        num_stories = Story.query.filter_by(author_id=2).count()
        self.assertEqual(self.get_context_variable('stats')[1][1], num_stories)
        # There aren't statistics for this user (num_reactions) 
        self.assertEqual(self.get_context_variable('stats')[0][1], 0)

        
        
class TestRegister(flask_testing.TestCase):
    app = None

    # First thing called
    def create_app(self):
      global app
        app = Flask(__name__, template_folder='../../templates')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
        app.config['SECRET_KEY'] = 'ANOTHER ONE'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['WTF_CSRF_ENABLED'] = False
        
        # app.config['LOGIN_DISABLED'] = True
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
      with app.app_context():
            # create an user
            user = db.session.query(User).filter(User.email == 'example@example.com').first()
            if user is None:
                example = User()
                example.firstname = 'Admin'
                example.lastname = 'Admin'
                example.email = 'example@example.com'
                example.dateofbirth = datetime.datetime(2010, 10, 5)
                example.is_admin = True
                example.set_password('admin')
                db.session.add(example)
                db.session.commit()
    
    # Executed at end of each test
    def tearDown(self) -> None:
        print("TEAR DOWN")
        db.session.remove()
        db.drop_all()

    # Test /users/create
    def test_register(self):

        # Register an user with an already used email
        payload = {'email': 'example@example.com',
                   'firstname': 'Admin',
                   'lastname': 'Admin',
                   'password': 'admin',
                   'dateofbirth': datetime.datetime(2010, 10, 10).strftime('%d/%m/%Y')}
        form = UserForm(data=payload)
        self.client.post('/users/create', data=form.data, follow_redirects=True)
        self.assert_template_used('create_user.html')
        self.assertEqual(self.get_context_variable('message'), 'The email address is already being used.')

        # Register an user with date of birth > today
        payload = {'email': 'example1@example.com',
                   'firstname': 'Admin',
                   'lastname': 'Admin',
                   'password': 'admin',
                   'dateofbirth': datetime.datetime(2020, 10, 10).strftime('%d/%m/%Y')}
        form = UserForm(data=payload)
        self.client.post('/users/create', data=form.data, follow_redirects=True)
        self.assert_template_used('create_user.html')
        self.assertEqual(self.get_context_variable('message'), 'Wrong date of birth.')

        # Test successful registration
        payload = {'email': 'example1@example.com',
                   'firstname': 'Admin',
                   'lastname': 'Admin',
                   'password': 'admin',
                   'dateofbirth': datetime.datetime(2010, 10, 10).strftime('%d/%m/%Y')}
        form = UserForm(data=payload)
        self.client.post('/users/create', data=form.data, follow_redirects=True)
        self.assert_template_used('users.html')
        new_user = db.session.query(User).filter(User.email == 'example1@example.com').first()
        self.assertIsNotNone(new_user)




if __name__ == '__main__':
    unittest.main()
    
