import json
import random as rnd
import unittest

from monolith.classes.DiceSet import Die, DiceSet


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
