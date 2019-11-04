import datetime
import unittest
from flask import Flask
from sqlalchemy.exc import IntegrityError

from monolith.forms import LoginForm
from monolith.views import blueprints
from monolith.auth import login_manager

import flask_testing

from monolith.database import Story, User, db, Follower


class TestDiceSet(flask_testing.TestCase):
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

        app.config['LOGIN_DISABLED'] = False
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

    def test_authorization(self):
        response = self.client.post('/users/logout')

        self.assert_redirects(response, '/')

        self.assert401(self.client.get('stories/new/settings'))
        self.assert401(self.client.post('stories/new/roll'))


    def test_dice_set(self):
        with app.app_context():
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            db.session.add(example)

            db.session.commit()

        payload = {'email': 'example@example.com',
                   'password': 'admin'}

        form = LoginForm(data=payload)

        self.assert200(self.client.post('/users/login', data=form.data, follow_redirects=True))

        # test settings template
        
        self.assert200(self.client.get('/stories/new/settings'))
        self.assert_template_used('settings.html')

        # test set not exist
        self.assertRedirects(self.client.post('/stories/new/roll', 
                            data={'dice_number': 2, 'dice_img_set': 'notexist'}), '/stories/new/settings')

        # test set not exist from same page with bad request key
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 2
            sess['dice_img_set'] = 'notexist'
            self.assertRedirects(self.client.post('/stories/new/roll', 
                            data={'dice_number': 2, 'dice_img_set': 'badrequestkey'}), '/stories/new/settings')

        # test set exist 
        self.client.post('/stories/new/roll', 
                            data={'dice_number': 2, 'dice_img_set': 'halloween'})
        self.assert_template_used('roll_dice.html')

        # test set exist from same page with bad request key
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 2
            sess['dice_img_set'] = 'animal'
            self.client.post('/stories/new/roll', 
                            data={'dice_img_set': 'badrequestkey'})
            self.assert_template_used('roll_dice.html')

    # Tests for POST, PUT and DEL requests ( /settings )
    def test_requests_settings(self):
        self.assert405(self.client.post('stories/new/settings'))
        self.assert405(self.client.put('stories/new/settings'))
        self.assert405(self.client.delete('stories/new/settings'))

    # Tests for GET, PUT and DEL requests ( /settings )
    def test_requests_roll(self):
        self.assert405(self.client.get('stories/new/roll'))
        self.assert405(self.client.put('stories/new/roll'))
        self.assert405(self.client.delete('stories/new/roll'))