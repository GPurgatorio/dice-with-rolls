import datetime
import flask_testing

from flask import Flask
from monolith.app import app as my_app
from monolith.views import blueprints
from monolith.forms import LoginForm
from monolith.auth import login_manager
from monolith.database import Story, User, db
import unittest


class TestLoginLogout(flask_testing.TestCase):
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
            # create an user Admin
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

    def test_login_logout(self):

        # Test login with an unexisting email
        payload = {'email': 'unexisting@example.com',
                   'password': 'admin'}
        form = LoginForm(data=payload)
        self.client.post('/users/login', data=form.data, follow_redirects=True)
        self.assert_template_used('login.html')
        self.assertEqual(self.get_context_variable('message'), 'This email does not exist.')

        # Test login with wrong password
        payload = {'email': 'example@example.com',
                   'password': 'wrong'}
        form = LoginForm(data=payload)
        self.client.post('/users/login', data=form.data, follow_redirects=True)
        self.assert_template_used('login.html')
        self.assertEqual(self.get_context_variable('message'), 'Password is uncorrect.')

        # Test successful login
        payload = {'email': 'example@example.com',
                   'password': 'admin'}
        form = LoginForm(data=payload)
        self.client.post('/users/login', data=form.data, follow_redirects=True)
        self.assert_template_used('index.html')
        all_stories = db.session.query(Story).all()
        self.assertEqual(self.get_context_variable('stories').all(), all_stories)

        # Test successful logout
        self.client.post('/users/logout', follow_redirects=True)
        self.assert_template_used('index.html')
        self.assertIsNone(self.get_context_variable('stories'))




if __name__ == '__main__':
    unittest.main()