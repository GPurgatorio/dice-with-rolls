import flask_testing
from flask import session
from monolith.app import app as my_app

class TestStories(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_stories(self):
        self.client.get('/stories')
        self.assert_200(self.client.get('/stories'))
        self.assert_template_used('stories.html')

    def test_write_story(self):
        #test write without roll dice
        self.assert200(self.client.get('/stories/write'))
        self.assert_template_used('roll_dice.html')
        #test write with session setted
        session['figures'] = ['beer',  'sea', 'train']
        self.assert200(self.client.get('/stories/write'))
        self.assert_template_used('write_story.html')







