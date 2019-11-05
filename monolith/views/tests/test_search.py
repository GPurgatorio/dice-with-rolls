import unittest
import json
from flask import request, jsonify, g, current_app
import flask_testing
from flask_login import login_user, current_user

from monolith.app import app as my_app
from monolith.database import db, Story, Reaction, ReactionCatalogue, Counter, User
from monolith.forms import LoginForm


class TestReaction(flask_testing.TestCase):

    def create_app(self):
        my_app.config['WTF_CSRF_ENABLED'] = False
        my_app.login_manager.init_app(my_app)

        return my_app

    def test1(self):
        self.client.get('http://127.0.0.1:5000/search/query/cat')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 2)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)

        self.client.get('http://127.0.0.1:5000/search/query/admin')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 0)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 1)

        self.client.get('http://127.0.0.1:5000/search/query/fgfdgfdhgdh')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 0)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)
