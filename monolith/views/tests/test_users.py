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

    #def test_user_statistics(self):
        # self.client.get('/users/2')
        # #self.assert_template_used('wall.html')
        # test_user = User.query.filter_by(id=2)
        # self.assertEqual(self.get_context_variable('user_info').id, test_user.id)
        # test_stats = [('avg_reactions', 0.0), ('num_reactions', 0), ('num_stories', 2), ('avg_dice', 2.0)]
        # self.assertEqual(self.get_context_variable('stats'), test_stats)
