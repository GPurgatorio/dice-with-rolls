import os
import random as rnd

from flask import Blueprint, session, render_template, request, flash, redirect, url_for
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
    # check dice_number
    try:
        # get number of dice from the form of previous page
        dice_number = int(request.form['dice_number'])
        session['dice_number'] = dice_number

        # check retrieved data
        if dice_number not in range(2, 7):
            raise ValueError

    except BadRequestKeyError:  # i'm here after re-rolling dice
        dice_number = session['dice_number']
    except (KeyError, ValueError):  # i'm here directly, have to go from settings before
        flash('Invalid number of dice!', 'error')
        session.pop('dice_number', None)
        return redirect(url_for('dice._settings'))

    # check dice_set
    try:
        # get dice set from the form of previous page
        dice_img_set = str(request.form['dice_img_set'])
        session['dice_img_set'] = dice_img_set

        # check retrieved data
        if dice_img_set not in {'standard', 'animal', 'halloween', 'emptyset'}:
            raise ValueError

    except BadRequestKeyError:  # i'm here after re-rolling dice
        dice_img_set = session['dice_img_set']
    except (KeyError, ValueError):  # i'm here directly, have to go from settings before
        flash('Invalid dice set!', 'error')
        session.pop('dice_img_set', None)
        return redirect(url_for('dice._settings'))

    # random sampling dice and throw them
    dice_indexes = rnd.sample(range(0, 6), dice_number)
    dice_list = []
    for i in dice_indexes:
        try:
            dirname = os.path.dirname(os.path.abspath(__file__))
            path = dirname + "/../resources/" + dice_img_set + "/"
            dice_list.append(Die(path + 'die' + str(i) + '.txt'))
        except (FileNotFoundError, IndexError):
            session.pop('dice_number', None)
            session.pop('dice_img_set', None)
            flash("Can't find dice on server", 'error')
            return redirect(url_for('dice._settings'))

    dice_set = DiceSet(dice_list)
    dice_set.throw_dice()
    session['figures'] = dice_set.pips

    context_vars = {'dice_number': dice_number, 'dice_img_set': dice_img_set, 'dice_indexes': dice_indexes,
                    'words': dice_set.pips, 'write_url': WRITE_URL, 'settings_url': SETTINGS_URL}
    return render_template('roll_dice.html', **context_vars)
