import json
import random as rnd


class Die:

    def __init__(self, filename):
        self.faces = []
        self.pip = None
        f = open(filename, "r")
        lines = f.readlines()
        for line in lines:
            self.faces.append(line.replace("\n", ""))
        self.throw_die()
        f.close()

    def throw_die(self):
        if self.faces:  # pythonic for list is not empty
            self.pip = rnd.choice(self.faces)
            return self.pip
        else:
            raise IndexError("throw_die(): empty die error.")


class DiceSet:

    def __init__(self, dice):
        self.dice = dice
        self.pips = []

    def serialize(self):
        return json.dumps(self.pips)

    def throw_dice(self):
        if not self.pips:  # check if list is empty, not assigned yet
            self.pips = [None] * (len(self.dice))
        for i in range(len(self.dice)):
            self.pips[i] = self.dice[i].throw_die()
        return self.pips
