import unittest

import flask_testing

from monolith.app import app as my_app
from monolith.database import db, User
from monolith.forms import LoginForm

import datetime

class TestDiceSet(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = False
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_dice_set(self):

        # create a test user
        with my_app.app_context():
            q = db.session.query(User).filter(User.email == 'test@test.com')
            user = q.first()
            if user is None:
                example = User()
                example.firstname = 'Test'
                example.lastname = 'Test'
                example.email = 'test@test.com'
                example.dateofbirth = datetime.datetime(2020, 10, 5)
                example.is_admin = False
                example.set_password('test')
                db.session.add(example)
                db.session.commit()

        # login with admin user
        payload = {'email': 'example@example.com',
                    'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

        # test settings template
        self.client.get('/stories/new/settings')
        #self.assert_template_used('settings.html')

        # test set not exist
        self.assertRedirects(self.client.post('/stories/new/roll', 
                            data={'dice_number': 2, 'dice_set': 'notexist'}), '/stories/new/settings')

        # test set not exist from same page with bad request key
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 2
            sess['dice_img_set'] = 'notexist'
            self.assertRedirects(self.client.post('/stories/new/roll', 
                            data={'dice_set': 'badrequestkey'}), '/stories/new/settings')

        # test set exist 
        self.client.post('/stories/new/roll', 
                            data={'dice_number': 2, 'dice_set': 'halloween'})
        self.assert_template_used('roll_dice.html')

        # test set not exist from same page with bad request key
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 2
            sess['dice_img_set'] = 'animal'
            self.client.post('/stories/new/roll', 
                            data={'dice_set': 'badrequestkey'})
            self.assert_template_used('roll_dice.html')

    # test authorization
    def test_athorization(self):
        self.assert401(self.client.get('stories/new/settings'))

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