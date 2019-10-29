import json
import random as rnd
import unittest

import flask_testing
from monolith.app import app as my_app
from monolith.database import Story


class TestTemplateStories(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_existing_story(self):
        self.client.get('/stories/1')
        self.assert_template_used('story.html')
        test_story = Story.query.filter_by(id=1).first()
        print('L\'oggetto da db: \n')
        print('User ID: ' + str(test_story.id))
        print('Author: ' + str(test_story.author))
        print('Date: ' + str(test_story.date))
        self.assertEqual(self.get_context_variable('story'), test_story)