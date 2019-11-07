import datetime

import flask_testing

from monolith.app import create_app
from monolith.database import User, db, Story
from monolith.urls import TEST_DB


class TestReaction(flask_testing.TestCase):
    app = None

    def create_app(self):
        global app
        app = create_app(TEST_DB)
        return app

    def setUp(self) -> None:
        with app.app_context():
            # user for login
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            db.session.add(example)
            db.session.commit()

            # reacted story
            test_story = Story()
            test_story.text = "Test story from admin user"
            test_story.author_id = 1
            test_story.is_draft = 0
            test_story.figures = "#admin#cat#"
            db.session.add(test_story)
            db.session.commit()

    def test_search(self):
        self.client.get('http://127.0.0.1:5000/search?query=cat')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 1)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)

        self.client.get('http://127.0.0.1:5000/search?query=admin')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 1)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 1)

        self.client.get('http://127.0.0.1:5000/search?query=nowords')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 0)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)
