import datetime
import json
import random as rnd
import unittest

import flask_testing
from monolith.app import app as my_app
from monolith.database import Story, User, db
from monolith.urls import RANGE_URL, LATEST_URL


class TestTemplateStories(flask_testing.TestCase):
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

            example2 = User()
            example2.firstname = 'Admin'
            example2.lastname = 'Admin'
            example2.email = 'example2@example2.com'
            example2.dateofbirth = datetime.datetime(2020, 10, 5)
            example2.is_admin = True
            example2.set_password('admin')
            db.session.add(example2)

            db.session.commit()

        payload = {'email': 'example@example.com',
                   'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

    # Executed at end of tests
    def tearDown(self) -> None:
        print("TEAR DOWN")
        db.session.remove()
        db.drop_all()

    def test_follow(self):
        response = self.client.post('/users/{}/follow'.format(2), follow_redirects=True)
        self.assert_template_used('wall.html')
        self.assert_message_flashed('Followed')

    def test_unfollow(self):
        self.client.post('/users/{}/follow'.format(2), follow_redirects=True)
        response = self.client.post('/users/{}/unfollow'.format(2), follow_redirects=True)
        self.assert_template_used('wall.html')
        self.assert_message_flashed('Unfollowed')

    def test_redirect_follow(self):
        response = self.client.post('/users/{}/follow'.format(2))
        self.assert_redirects(response, '/users/{}'.format(2))

    def test_redirect_unfollow(self):
        response = self.client.post('/users/{}/unfollow'.format(2))
        self.assert_redirects(response, '/users/{}'.format(2))

    def test_login_required(self):
        response = self.client.post('/users/logout')
        # Log out success
        self.assert_redirects(response, '/')
        response = self.client.post('/users/{}/follow'.format(2), follow_redirects=True)
        self.assert401(response, 'You must login to follow')

        response = self.client.post('/users/{}/unfollow'.format(2), follow_redirects=True)
        self.assert401(response, 'You must login to unfollow')

    # def test_user_statistics(self):


# self.client.get('/users/2')
# #self.assert_template_used('wall.html')
# test_user = User.query.filter_by(id=2)
# self.assertEqual(self.get_context_variable('user_info').id, test_user.id)
# test_stats = [('avg_reactions', 0.0), ('num_reactions', 0), ('num_stories', 2), ('avg_dice', 2.0)]
# self.assertEqual(self.get_context_variable('stats'), test_stats)


if __name__ == '__main__':
    unittest.main()
