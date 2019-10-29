import json
import random as rnd
import unittest

import flask_testing
from monolith.classes.DiceSet import Die
from monolith.app import app as my_app


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

    def test_words_length(self):

        self.client.get('/stories/dice/roll')
        self.assert_template_used('roll_dice.html')
        self.assertEqual(len(self.get_context_variable('words')), 6)
        self.assert_context('write_url', "http://127.0.0.1:5000/stories/write")


