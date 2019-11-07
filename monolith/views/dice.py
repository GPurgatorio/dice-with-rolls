import os
import random as rnd

from flask import Blueprint, jsonify, session, abort, render_template, request, flash, redirect, url_for
from flask_login import login_required
from werkzeug.exceptions import BadRequestKeyError

from monolith.classes.DiceSet import DiceSet, Die
from monolith.urls import WRITE_URL, ROLL_URL, SETTINGS_URL

dice = Blueprint('dice', __name__)


@dice.route('/stories/new/settings', methods=['GET'])
@login_required
def _settings():
    context_vars = {"roll_url": ROLL_URL}
    return render_template('settings.html', **context_vars)


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
    except (KeyError, ValueError):  # i'm here directly, have to go from settings before
        flash('Invalid number of dice!', 'error')
        session.pop('dice_number', None)
        return redirect(url_for('dice._settings'))

    # random sampling dice and throw them
    dice_indexes = rnd.sample(range(0, 6), dice_number)
    dice_list = []
    for i in dice_indexes:
        try:
            dirname = os.path.dirname(os.path.abspath(__file__))
            path = dirname + "/../resources/"
            dice_list.append(Die(path + 'die' + str(i) + '.txt'))
        except FileNotFoundError:
            print("File die" + str(i) + ".txt not found")
            session.pop('dice_number', None)
            flash("Can't find dice on server", 'error')
            return redirect(url_for('home.index'))

    dice_set = DiceSet(dice_list)
    try:
        dice_set.throw_dice()
    except IndexError:
        session.pop('dice_number', None)
        flash('Error in throwing dice', 'error')
        return redirect(url_for('home.index'))
    session['figures'] = dice_set.pips

<<<<<<< Updated upstream
    context_vars = {'dice_number': dice_number, 'words': dice_set.pips,
                    'write_url': WRITE_URL, 'settings_url': SETTINGS_URL}
=======
    context_vars = {'dice_number': dice_number, 'dice_img_set': dice_img_set, 'dice_indexes': dice_indexes,
                    'words': dice_set.pips, 'write_url': WRITE_URL, 'settings_url': SETTINGS_URL}
>>>>>>> Stashed changes
    return render_template('roll_dice.html', **context_vars)

