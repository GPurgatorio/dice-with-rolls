
from flask import session
import datetime
import json
import random as rnd
import unittest

import flask_testing
from flask_login import login_user, current_user

from monolith.app import app as my_app
from monolith.forms import LoginForm, StoryForm
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
        print('L\'oggetto da db: \n')
        print('User ID: ' + str(test_story.id))
        print('Author: ' + str(test_story.author))
        print('Date: ' + str(test_story.date))
        self.assertEqual(self.get_context_variable('story'), test_story)
        
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
        print(d)
        req_stories = Story.query.filter(Story.date >= d).all()
        for s in req_stories:
            print(s.date)
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


class TestStories(flask_testing.TestCase):

    def create_app(self):
        my_app.config['WTF_CSRF_ENABLED'] = False
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_stories(self):
        self.client.get('/stories')
        self.assert_200(self.client.get('/stories'))
        self.assert_template_used('stories.html')

    def test_write_story(self):
        payload = {'email': 'example@example.com',
                   'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

        # test write without rolling dice
        self.assert_redirects(self.client.get('/stories/new/write'), '/')
        self.client.get('/stories/new/write', follow_redirects=True)
        self.assert_template_used('index.html')

        # test write with right session
        with self.client.session_transaction() as session:
            session['figures'] = ['beer', 'cat', 'dog']
        self.assert200(self.client.get('/stories/new/write'))
        self.assert_template_used('write_story.html')

        # test write with invalid story
        payload = {'text': 'my cat is drinking a gin tonic with my neighbour\'s dog'}
        form = StoryForm(data=payload)
        response = self.client.post('/stories/new/write', data=form.data)
        self.assert400(response)
        self.assert_template_used('write_story.html')
        self.assert_context('message', 'Your story doesn\'t contain all the words. Missing: beer ')

        # test write story with valide one
        payload1 = {'text': 'my cat is drinking a beer with my neighbour\'s dog'}
        form1 = StoryForm(data=payload1)
        response = self.client.post('/stories/new/write', data=form1.data, follow_redirects=True)
        self.assert_status(response, 200)
        self.assert_template_used('stories.html')

        # test write story with draft id
        draft = Story()
        draft.author_id = 1
        draft.figures = 'dog#cat#beer'
        draft.text = 'halloween bye bye'
        draft.is_draft = True
        db.session.add(draft)
        db.session.commit()
        draft_db = Story.query.filter(Story.figures == 'dog#cat#beer', Story.text == 'halloween bye bye',
                                      Story.author_id == 1).first()

        url = '/stories/new/write/' + str(draft_db.id)
        response = self.client.get(url)
        self.assert200(response)
        self.assert_template_used('write_story.html')

        response = self.client.post(url, data=form1.data, follow_redirects=True)
        self.assert200(response)
        self.assert_template_used('stories.html')
        self.assertEqual(draft_db.is_draft, False)
        self.assertEqual(draft_db.text, 'my cat is drinking a beer with my neighbour\'s dog')

        # test write story with invalid draft (not yours)
        response = self.client.post(url, data=form1.data)
        self.assert_status(response, 302)
        # test write story with invalid draft (not draft)
        response = self.client.post(url, data=form1.data)
        self.assert_status(response, 302)
        self.assert_template_used('stories.html')
