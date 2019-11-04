import flask_testing

from monolith.app import app as my_app
from monolith.database import db, User
from monolith.forms import LoginForm

import datetime

class TestTemplateOtherWall(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = False
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_user_wall(self):
        # looking for non-existing user without login
        id = 10
        self.client.get('/users/' + str(id))
        self.assert_template_used('wall.html')
        self.assertEqual(self.get_context_variable('exists'), False)

        # looking for existing user without login
        id = 1
        self.client.get('/users/' + str(id))
        self.assert_template_used('wall.html')
        self.assertEqual(self.get_context_variable('exists'), True)
        user_info = User.query.filter_by(id=id).first()
        self.assertEqual(self.get_context_variable('user_info'), user_info)

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

        # looking for non-existing user after login
        id = 10
        self.client.get('/users/' + str(id))
        self.assert_template_used('wall.html')
        self.assertEqual(self.get_context_variable('exists'), False)

        # looking for existing user after login
        id = 2
        self.client.get('/users/' + str(id))
        self.assert_template_used('wall.html')
        self.assertEqual(self.get_context_variable('exists'), True)
        user_info = User.query.filter_by(id=id).first()
        self.assertEqual(self.get_context_variable('user_info'), user_info)

        # looking for owned wall after login
        id = 1
        self.client.get('/users/' + str(id))
        self.assert_template_used('wall.html')
        self.assertEqual(self.get_context_variable('exists'), True)
        user_info = User.query.filter_by(id=id).first()
        self.assertEqual(self.get_context_variable('user_info'), user_info)

    # test method not allowed
    def test_methods_wall(self):
        self.assert405(self.client.post('/users/1'))
        self.assert405(self.client.put('/users/1'))
        self.assert405(self.client.delete('/users/1'))