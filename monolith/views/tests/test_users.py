import flask_testing
import unittest
from flask import Flask
from monolith.views import blueprints
from monolith.database import db
from monolith.auth import login_manager
#from monolith.app import app as my_app, db


class TestTemplateStories(flask_testing.TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_storytellers.db"
    TESTING = True

    #First thing called
    def create_app(self):
        app = Flask(__name__)
        app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
        app.config['SECRET_KEY'] = 'ANOTHER ONE'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storytellers.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        for bp in blueprints:
            app.register_blueprint(bp)
            bp.app = app

        db.init_app(app)
        login_manager.init_app(app)
        db.create_all(app=app)
        print("CREATE APP")
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        return my_app

    # Set up database for testing here
    def setUp(self) -> None:
        print("SET UP")
        db.create_all()

    #Executed at end of tests
    def tearDown(self) -> None:
        print("TEAR DOWN")
        db.session.remove()
        db.drop_all()

    def test_follow(self):
        print("TEST_FOLLOW")
        assert True


if __name__ == '__main__':
    unittest.main()
