import os
import random as rnd

from flask import Blueprint, jsonify, session, abort, render_template, request, flash, redirect, url_for
from flask_login import login_required
from werkzeug.exceptions import BadRequestKeyError

from monolith.classes.DiceSet import DiceSet, Die

dice = Blueprint('dice', __name__)


@dice.route('/stories/new/settings', methods=['GET'])
@login_required
def _settings():
    return render_template('settings.html', roll_url="http://127.0.0.1:5000/stories/new/roll")


@dice.route('/stories/new/roll', methods=['POST'])
@login_required
def _roll_dice():

    try:
        # get number of dice from the form of previous page
        dice_number = int(request.form['dice_number'])
        session['dice_number'] = dice_number
        if dice_number not in range(2, 7):
            raise ValueError
    except BadRequestKeyError:  # i'm here after re-rolling dice
        dice_number = session['dice_number']
    except ValueError:
        flash('Invalid number of dice!', 'error')
        session.clear()
        return redirect(url_for('_settings'))

    # random sampling dice and throw them
    dice_indexes = rnd.sample(range(0, 6), dice_number)
    dice_list = []
    for i in dice_indexes:
        try:
            dice_list.append(Die('monolith/resources/die' + str(i) + '.txt'))
        except FileNotFoundError:
            print("File die" + str(i) + ".txt not found")
            session.clear()
            return redirect(url_for('stories._stories', message="Can't find dice on server"))
    dice_set = DiceSet(dice_list)
    try:
        dice_set.throw_dice()
    except IndexError as e:
        # flash('Error in throwing dice', 'error')
        session.clear()
        return redirect(url_for('stories._stories', message='Error in throwing dice'))
    session['figures'] = dice_set.pips
    return render_template('roll_dice.html', words=dice_set.pips, write_url="http://127.0.0.1:5000/stories/new/write")
