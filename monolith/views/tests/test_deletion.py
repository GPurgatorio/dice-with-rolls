import unittest
import json
from flask import request, jsonify, g, current_app
import flask_testing
from flask_login import login_user, current_user

from monolith.app import app as my_app
from monolith.database import db, Story, User
from monolith.forms import LoginForm


class TestReaction(flask_testing.TestCase):

    def create_app(self):
        my_app.config['WTF_CSRF_ENABLED'] = False
        my_app.login_manager.init_app(my_app)

        return my_app

    def test1(self):
        payload = {'email': 'example@example.com',
                   'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

        test_story = Story()
        test_story.text = "Test story from admin user"
        test_story.author_id = 1
        test_story.is_draft = 0
        test_story.figures = "Test#admin"

        db.session.add(test_story)
        db.session.commit()

        story_id = Story.query.filter(Story.text == "Test story from admin user").first().id

        self.client.post('/stories/' + str(story_id))
        self.assert_template_used('stories.html')
        self.assert_context('message', '')

        self.assertEqual(len(Story.query.filter(Story.id == story_id).all()), 0)

        other_story_id = Story.query.filter(Story.id != story_id).first().id

        self.client.post('/stories/' + str(other_story_id))
        self.assert_template_used('stories.html')
        self.assert_context('message', 'Cannot delete other user\'s story')

        self.assertEqual(len(Story.query.filter(Story.id == other_story_id).all()), 1)

