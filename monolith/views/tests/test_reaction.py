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
        len_to_be_deleted_reactions = len(Reaction.query.filter(Reaction.story_id == '1', Reaction.reactor_id == 1, Reaction.marked == 2).all())

        payload = {'email': 'example@example.com',
                            'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

        self.client.post('http://127.0.0.1:5000/stories/react/1/Like')

        self.assert_template_used('stories.html')
        unmarked_reactions = Reaction.query.filter(Reaction.story_id == '1', Reaction.reactor_id == 1,  Reaction.marked == 0).all()
        self.assertEqual(len(unmarked_reactions), 1)
        self.assertEqual(unmarked_reactions[0].reaction_type_id, 1)

        self.client.post('http://127.0.0.1:5000/stories/react/1/Like')
        self.assert_template_used('stories.html')
        self.assert_context('message', 'You have already reacted this story')

        self.client.post('http://127.0.0.1:5000/stories/react/1/Dislike')
        self.assert_template_used('stories.html')
        unmarked_reactions = Reaction.query.filter(Reaction.story_id == '1', Reaction.marked == 0).all()
        self.assertEqual(unmarked_reactions[0].reaction_type_id, 2)
        self.assertEqual(len(unmarked_reactions), 1)

        Reaction.query.filter(Reaction.story_id == '1', Reaction.marked == 0).first().marked = 1
        db.session.commit()

        self.client.post('http://127.0.0.1:5000/stories/react/1/Like')
        unmarked_reactions = Reaction.query.filter(Reaction.story_id == '1', Reaction.reactor_id == 1, Reaction.marked == 0).all()
        marked_reactions = Reaction.query.filter(Reaction.story_id == '1', Reaction.reactor_id == 1,Reaction.marked == 1).all()
        to_be_deleted_reactions = Reaction.query.filter(Reaction.story_id == '1', Reaction.reactor_id == 1, Reaction.marked == 2).all()

        self.assertEqual(len(unmarked_reactions), 1)
        self.assertEqual(len(marked_reactions), 0)
        self.assertEqual(len(to_be_deleted_reactions), len_to_be_deleted_reactions + 1)




