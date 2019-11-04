import datetime
import flask_testing
from monolith.app import app as my_app
from monolith.database import db, Story, User
from monolith.forms import LoginForm


class TestDeletion(flask_testing.TestCase):

    def create_app(self):
        my_app.config['WTF_CSRF_ENABLED'] = False
        my_app.login_manager.init_app(my_app)

        return my_app

    def test1(self):
        payload = {'email': 'example@example.com',
                   'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

        dummy_user = User()
        dummy_user.firstname = 'Dummy'
        dummy_user.lastname = 'Dummy'
        dummy_user.email = 'dummy@example.com'
        dummy_user.dateofbirth = datetime.datetime(2020, 10, 5)
        dummy_user.is_admin = True
        dummy_user.set_password('admin')
        db.session.add(dummy_user)
        db.session.commit()

        dummy_id = User.query.filter(User.email == 'dummy@example.com').first().id

        test_story = Story()
        test_story.text = "Test story from admin user"
        test_story.author_id = 1
        test_story.is_draft = 0
        test_story.figures = "Test#admin"

        dummy_story = Story()
        dummy_story.text = "Test story from dummy user"
        dummy_story.author_id = dummy_id
        dummy_story.is_draft = 0
        dummy_story.figures = "Test#dummy"

        db.session.add(test_story)
        db.session.add(dummy_story)
        db.session.commit()

        story_id = Story.query.filter(Story.text == "Test story from admin user").first().id
        dummy_story_id = Story.query.filter(Story.author_id == dummy_id).first().id

        self.client.post('/stories/delete/' + str(story_id))
        self.assert_template_used('index.html')

        self.assertEqual(len(Story.query.filter(Story.id == story_id).all()), 0)

        self.client.post('/stories/delete/' + str(dummy_story_id))
        self.assert_template_used('index.html')
        self.assert_message_flashed("Cannot delete other user's story", 'error')

        self.assertEqual(len(Story.query.filter(Story.id == dummy_story_id).all()), 1)
