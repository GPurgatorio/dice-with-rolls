from datetime import datetime, timedelta
from random import randint

from flask import Blueprint, redirect, render_template, request, abort, session
from monolith.database import db, Story
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm, StoryForm

stories = Blueprint('stories', __name__)


@stories.route('/stories')
def _stories(message=''):
    allstories = db.session.query(Story)

    return render_template("stories.html", message=message, stories=allstories,
                           like_it_url="http://127.0.0.1:5000/stories/like/")

  
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
    return render_template("write_story.html", submit_url="http://127.0.0.1:5000/stories/new/submit", form=form,
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
   
    
@stories.route('/stories/random', methods=['GET'])
def _random_story():
    #return render_template("no_recent_stories.html", write_url="http://127.0.0.1:5000/stories/new/roll")
    # get all the stories written in the last three days 
    begin = (datetime.now() - timedelta(3)).date()
    recent_stories = db.session.query(Story).filter(Story.date >= begin).all()
    # pick a random story from them
    if len(recent_stories)==0:
        return render_template("no_recent_stories.html", write_url="http://127.0.0.1:5000/stories/new/roll")
    else:
        pos = randint(0, len(recent_stories)-1)
        return _open_story(recent_stories[pos].id)

        


