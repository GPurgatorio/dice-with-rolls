import unittest
import json
from flask import request, jsonify
import flask_testing
from flask_login import login_user

from monolith.app import app as my_app
from monolith.database import db, Story, Reaction, ReactionCatalogue, Counter, User




class TestReaction(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        q = db.session.query(User).filter(User.email == 'example@example.com')
        user = q.first()
        print(q.first().id)
        if user is not None and user.authenticate('admin'):
            login_user(user)
        return my_app

    def test1(self):
        self.client.get('/stories')
        self.assert_template_used('stories.html')
        allstories = db.session.query(Story).all()
        self.assertEqual(self.get_context_variable('stories').all(), allstories)

