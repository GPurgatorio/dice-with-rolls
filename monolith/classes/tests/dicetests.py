from monolith.classes.DiceSet import Die, DiceSet
import unittest
import random as rnd

class TestDie(unittest.TestCase):

    # Open a non existing file
    def test_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            die = Die("abc.txt")

    # Open an existing file
    def test_init_die(self):
        die = Die("die0.txt")
        expected_faced = ['bike', 'moonandstars', 'bag', 'bird', 'crying', 'angry']
        self.assertEqual(die.faces, expected_faced)

    # Open an empty file (IndexError)
    def test_empty_die(self):
        with self.assertRaises(IndexError):
            die = Die("dieEmpty.txt")

    # Test the throw_die() method
    def test_throw_die(self):
        die = Die("die0.txt")
        rnd.seed(574891)
        result = die.throw_die()
        self.assertEqual(result, 'bird')

class TestDiceSet(unittest.TestCase):

    def test_empty_dice(self):
        with self.assertRaises(TypeError):
            dice = DiceSet()

    def test_throw_dice(self):
        rnd.seed(574891)
        die1 = Die("die0.txt")
        die2 = Die("die1.txt")
        die3 = Die("die2.txt")
        dice = [die1, die2, die3]
        dice_set = DiceSet(dice)
        expected_res = ['bag', 'clock', 'bus']
        self.assertEqual(dice_set.throw_dice(), expected_res)

 
if __name__ == '__main__':
    unittest.main()
