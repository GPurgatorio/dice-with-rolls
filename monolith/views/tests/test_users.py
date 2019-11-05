import datetime
from flask import Flask, blueprints
import flask_testing

from monolith.auth import login_manager
from monolith.views import blueprints
from monolith.database import Story, User, db, ReactionCatalogue, Counter
from monolith.forms import LoginForm


class TestUsers(flask_testing.TestCase):
    app = None

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
            example.is_draft = False
            db.session.add(example)
            db.session.commit()

            example = Story()
            example.text = 'Another story!'
            example.author_id = 1
            example.figures = 'another#story'
            example.is_draft = False
            db.session.add(example)
            db.session.commit()

            # Add some drafts for user 1
            example = Story()
            example.text = 'Trial story :)'
            example.author_id = 1
            example.figures = 'example#admin'
            example.is_draft = True
            db.session.add(example)
            db.session.commit()

            # Add some drafts for user 2
            example = Story()
            example.text = 'Trial story :)'
            example.author_id = 2
            example.figures = 'example#admin'
            example.is_draft = True
            db.session.add(example)
            db.session.commit()

        # login
        payload = {'email': 'example@example.com',
                   'password': 'admin'}
        form = LoginForm(data=payload)
        self.client.post('/users/login', data=form.data, follow_redirects=True)

    # Executed at end of each test
    def tearDown(self) -> None:
        print("TEAR DOWN")
        db.session.remove()
        db.drop_all()

    def test_user_stories(self):
        # Testing stories of not existing user
        response = self.client.get('/users/100/stories')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://127.0.0.1:5000/')

        # Testing stories of existing user
        response = self.client.get('/users/1/stories')
        self.assert200(response)
        self.assert_template_used('user_stories.html')

    def test_user_drafts(self):
        # Testing stories of not existing user
        response = self.client.get('/users/100/drafts')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://127.0.0.1:5000/')

        # Testing stories of other user
        response = self.client.get('/users/2/drafts')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://127.0.0.1:5000/')

        # Testing stories of existing user
        response = self.client.get('/users/1/drafts')
        self.assert200(response)
        self.assert_template_used('drafts.html')
