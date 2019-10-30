import datetime

from flask import Blueprint, redirect, render_template, request, abort, session
from sqlalchemy import func, desc, asc

from monolith.database import db, Story
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm, StoryForm
from monolith.urls import SUBMIT_URL, REACTION_URL, LATEST_URL, RANGE_URL

stories = Blueprint('stories', __name__)


@stories.route('/stories')
def _stories(message=''):
    allstories = db.session.query(Story)
    context_vars = {"message": message, "stories": allstories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL}
    return render_template("stories.html", **context_vars)


@stories.route('/stories/latest', methods=['GET'])
def _latest(message=''):
    # stories = db.session.query(Story).order_by(desc(Story.date))      ALL STORIES IN GOOD ORDER
    ##subq = db.session.query(func.max(Story.date).label('max_date'), Story.author_id).group_by(Story.author_id).subquery('t1')
    #stories = db.session.query(Story).group_by(Story.author_id, Story.date).order_by(Story.date.desc(), Story.author_id)
    ##stories = db.session.query(Story).join(subq, Story.author_id == subq.c.author_id)
    stories = db.engine.execute("SELECT * FROM story s1 WHERE s1.date = (SELECT MAX (s2.date) FROM story s2 WHERE s1.author_id == s2.author_id) ORDER BY s1.author_id")
    return render_template('stories.html', message=message, stories=stories)

@stories.route('/stories/range', methods=['GET'])
def _range(message=''):
    begin = request.args.get('begin')
    end = request.args.get('end')
    try:
        begin_date = datetime.datetime.strptime(begin, '%d-%m-%Y').date()
        end_date = datetime.datetime.strptime(end, '%d-%m-%Y').date()
    except ValueError:
        return render_template('stories.html', message='Wrong URL parameters.')
    if begin_date > end_date:
        return render_template('stories.html', message='Begin date cannot be higher than End date')
    stories = db.session.query(Story).filter(Story.date >= begin_date).filter(Story.date <= end_date)
    return render_template('stories.html', message=message, stories=stories)

# Open a story functionality (1.8)
@stories.route('/stories/<int:id_story>', methods=['GET'])
def _open_story(id_story):
    # Get the story object from database
    story = Story.query.filter_by(id=id_story).first()
    if story is not None:
        rolled_dice = story.figures.split('#')
        # TODO : aggiornare per le reactions
        return render_template('story.html', exists=True, story=story, rolled_dice=rolled_dice)
    else:
        return render_template('story.html', exists=False)


@stories.route('/stories/new/write', methods=['GET', 'POST'])
@login_required
def _write_story(message=''):
    form = StoryForm()
    # prendi parole dalla sessione
    figures = session['figures']
    return render_template("write_story.html", submit_url=SUBMIT_URL, form=form,
                           words=figures, message=message)


@stories.route('/stories/submit', methods=['POST'])
@login_required
def _submit_story():
    form = StoryForm()
    result = ''
    if form.validate_on_submit():
        new_story = Story()
        new_story.author_id = current_user.id
        new_story.figures = '#'.join(session['figures'])
        form.populate_obj(new_story)
        story_words = form['text'].data.split(' ')
        if len(story_words) == 0:
            result = 'Your story is empty'
        else:
            counter = 0
            for w in story_words:
                if w in session['figures']:
                    counter += 1
            if counter == len(session['figures']):
                result = 'Your story is a valid one! It has been published'
                db.session.add(new_story)
                db.session.commit()
                return _stories(message=result)
            else:
                result = 'Your story doesn\'t contain all the words '

    return _write_story(message=result)
