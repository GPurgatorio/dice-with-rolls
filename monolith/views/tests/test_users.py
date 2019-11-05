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


class TestTemplateStories(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        return my_app

    #def test_user_statistics(self):
        # self.client.get('/users/2')
        # #self.assert_template_used('wall.html')
        # test_user = User.query.filter_by(id=2)
        # self.assertEqual(self.get_context_variable('user_info').id, test_user.id)
        # test_stats = [('avg_reactions', 0.0), ('num_reactions', 0), ('num_stories', 2), ('avg_dice', 2.0)]
        # self.assertEqual(self.get_context_variable('stats'), test_stats)

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