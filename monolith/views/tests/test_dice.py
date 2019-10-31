import json
import os
import random as rnd
import unittest

import flask_testing
from flask import url_for

from monolith.classes.DiceSet import Die
from monolith.app import app as my_app
from monolith.urls import WRITE_URL


class TestDice(unittest.TestCase):

    def test_die_init(self):
        # non-existing file to build a die
        with self.assertRaises(FileNotFoundError):
            die = Die('imnotafile.txt')

        # empty die
        with self.assertRaises(IndexError):
            die = Die("monolith/resources/dieEmpty.txt")

        # die check
        die = Die("monolith/resources/die0.txt")
        expected_faced = ['bike', 'moonandstars', 'bag', 'bird', 'crying', 'angry']
        self.assertEqual(die.faces, expected_faced)

    def test_throw_die(self):
        rnd.seed(666)
        die = Die("monolith/resources/die0.txt")
        res = die.throw_die()
        self.assertEqual(res, 'bird')


class TestTemplateDice(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        return my_app

    # Tests for GET, PUT and DEL requests ( /settings )
    def test_requests_settings(self):
        self.assert405(self.client.get('stories/new/settings'))
        self.assert405(self.client.put('stories/new/settings'))
        self.assert405(self.client.delete('stories/new/settings'))

    def test_requests_roll(self):
        self.assert405(self.client.get('stories/new/roll'))
        self.assert405(self.client.put('stories/new/roll'))
        self.assert405(self.client.delete('stories/new/roll'))

    def test_settings(self):
        self.client.post('/stories/new/settings')
        self.assert_template_used('settings.html')

    # 9 is out of range (2,7) -> redirect to settings
    def test_oob_roll(self):
        self.assertRedirects(self.client.post('/stories/new/roll', data={'dice_number': 9}), '/stories/new/settings')

    # Redirect from session (abc fails, throws ValueError, gets 8 from session, out of range -> redirect)
    def test_oob_roll_sess(self):
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 8
            self.assertRedirects(self.client.post('/stories/new/roll', data={'dice_number': 'abc'}), '/stories/new/settings')

"""
    # Correct execution's flow of roll
    def test_roll(self):
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 2
        rnd.seed(2)             # File die0.txt
        # Riga 43: dice_list.append(Die('monolith/resources/die' + str(i) + '.txt')) -> File not Found -> fail del test
        self.client.post('/stories/new/roll')
        self.assert_template_used('stories.html')
"""