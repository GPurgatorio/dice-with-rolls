import json
import random as rnd
import unittest

import flask_testing
from flask import session
from monolith.app import app as my_app
from monolith.database import Story

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

    def test_existing_story(self):
        self.client.get('/stories/1')
        self.assert_template_used('story.html')
        test_story = Story.query.filter_by(id=1).first()
        print('L\'oggetto da db: \n')
        print('User ID: ' + str(test_story.id))
        print('Author: ' + str(test_story.author))
        print('Date: ' + str(test_story.date))
        self.assertEqual(self.get_context_variable('story'), test_story)