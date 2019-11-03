import datetime
import json
import random as rnd
import unittest

import flask_testing
from monolith.app import app as my_app
from monolith.database import Story, User, db
from monolith.urls import RANGE_URL, LATEST_URL


class TestTemplateStories(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_existing_story(self):
        self.client.get('/stories/1')
        self.assert_template_used('story.html')
        test_story = Story.query.filter_by(id=1).first()
        self.assertEqual(self.get_context_variable('story'), test_story)

    def test_non_existing_story(self):
        self.client.get('/stories/500')
        self.assert_template_used('story.html')
        self.assertEqual(self.get_context_variable('exists'), False)

    def test_latest_story(self):
        # testing that the total number of users is higher than the number of latest stories per user
        self.client.get(LATEST_URL)
        self.assert_template_used('stories.html')
        # req_stories = db.engine.execute("SELECT * FROM story s1 WHERE s1.date = (SELECT MAX (s2.date) FROM story s2 WHERE s1.author_id == s2.author_id) ORDER BY s1.author_id")
        num_users = len(db.session.query(User).all())
        self.assertLessEqual(self.get_context_variable('stories').rowcount, num_users)

    def test_range_story(self):
        # testing range without parameters
        self.client.get(RANGE_URL)
        self.assert_template_used('stories.html')
        all_stories = db.session.query(Story).all()
        self.assertEqual(self.get_context_variable('stories').all(), all_stories)

        # testing range with only one parameter (begin)
        self.client.get(RANGE_URL + '?begin=2013-10-10')
        d = datetime.datetime.strptime('2013-10-10', '%Y-%m-%d')
        req_stories = Story.query.filter(Story.date >= d).all()
        self.assertEqual(self.get_context_variable('stories').all(), req_stories)

        # testing range with only one parameter (end)
        self.client.get(RANGE_URL + '?end=2013-10-10')
        e = datetime.datetime.strptime('2013-10-10', '%Y-%m-%d')
        req_stories = Story.query.filter(Story.date <= e).all()
        self.assertEqual(self.get_context_variable('stories').all(), req_stories)

        # testing range with begin date > end date
        self.client.get(RANGE_URL + '?begin=2012-12-12&end=2011-10-10')
        self.assertEqual(self.get_context_variable('message'), 'Begin date cannot be higher than End date')

        # testing range (valid req)
        d = datetime.datetime.strptime('2012-10-15', '%Y-%m-%d')
        e = datetime.datetime.strptime('2020-10-10', '%Y-%m-%d')
        self.client.get(RANGE_URL + '?begin=2012-10-15&end=2020-10-10')
        req_stories = Story.query.filter(Story.date >= d).filter(Story.date <= e).all()
        self.assertEqual(self.get_context_variable('stories').all(), req_stories)
