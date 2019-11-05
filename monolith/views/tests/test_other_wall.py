import datetime
import unittest

import flask_testing

from monolith.database import User, db
from monolith.forms import LoginForm
from monolith.app import create_test_app

class TestTemplateOtherWall(flask_testing.TestCase):
    app = None

    # First thing called
    def create_app(self):
        global app
        app = create_test_app()
        return app

    # Set up database for testing
    def setup_DB(self) -> None:
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

    def test_wall_nologin(self):
        response = self.client.post('/users/logout')
        # Log out success
        self.assert_redirects(response, '/')

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

    def test_wall_login(self):
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

        # looking for personal wall after login
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


if __name__ == '__main__':
    unittest.main()