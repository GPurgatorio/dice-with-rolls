import json
import os
import random as rnd
import unittest

import flask_testing

from monolith.app import create_test_app
from monolith.classes.DiceSet import Die, DiceSet

path = os.path.dirname(os.path.abspath(__file__)) + "/../../resources/"


class TestDice(unittest.TestCase):

    def test_die_init(self):
        global path
        # non-existing file to build a die
        with self.assertRaises(FileNotFoundError):
            Die('imnotafile.txt')

        # empty die
        with self.assertRaises(IndexError):
            Die(path+"dieEmpty.txt")

        # die check
        die = Die(path+"die0.txt")
        expected_faced = ['bike', 'moonandstars', 'bag', 'bird', 'crying', 'angry']
        self.assertEqual(die.faces, expected_faced)

    def test_throw_die(self):
        rnd.seed(666)
        die = Die(path + "die0.txt")
        res = die.throw_die()
        self.assertEqual(res, 'bird')


class TestDiceSet(unittest.TestCase):

    def test_empty_dice_set(self):
        with self.assertRaises(TypeError):
            DiceSet()

    def test_throw_and_serialize_dice_set(self):
        rnd.seed(574891)
        die1 = Die(path+"die0.txt")
        die2 = Die(path+"die1.txt")
        die3 = Die(path+"die2.txt")
        dice = [die1, die2, die3]
        dice_set = DiceSet(dice)

        # throw dice
        expected_res = ['bag', 'clock', 'bus']
        self.assertEqual(dice_set.throw_dice(), expected_res)

        # serialize set
        serialized_set = dice_set.serialize()
        expected_serialized_set = json.dumps(dice_set.pips)
        self.assertEqual(serialized_set, expected_serialized_set)


class TestTemplateDice(flask_testing.TestCase):

    app = None

    # First thing called
    def create_app(self):
        global app
        app = create_test_app(login_disabled=True)
        return app

    # Tests for POST, PUT and DEL requests ( /settings )
    def test_requests_settings(self):
        self.assert405(self.client.post('stories/new/settings'))
        self.assert405(self.client.put('stories/new/settings'))
        self.assert405(self.client.delete('stories/new/settings'))

    def test_requests_roll(self):
        self.assert405(self.client.get('stories/new/roll'))
        self.assert405(self.client.put('stories/new/roll'))
        self.assert405(self.client.delete('stories/new/roll'))

    def test_settings(self):
        self.client.get('/stories/new/settings')
        self.assert_template_used('settings.html')

    # 9 is out of range (2,7) -> redirect to settings
    def test_oob_roll(self):
        result = self.client.post('/stories/new/roll', data={'dice_number': 9})
        self.assertRedirects(result, '/stories/new/settings')

    # Redirect from session (abc fails, throws ValueError, gets 8 from session, out of range -> redirect)
    def test_oob_roll_sess(self):
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 8
            result = self.client.post('/stories/new/roll', data={'dice_number': 'abc'})
            self.assertRedirects(result, '/stories/new/settings')

    # Correct execution's flow of roll
    def test_roll(self):
        with self.client.session_transaction() as sess:
            sess['dice_number'] = 2
        rnd.seed(2)             # File die0.txt
        self.client.post('/stories/new/roll')
        self.assert_template_used('roll_dice.html')
