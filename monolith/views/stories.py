from flask import Blueprint, redirect, render_template, request, abort, session
from monolith.database import db, Story, Like
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


@stories.route('/stories/like/<authorid>/<storyid>')
@login_required
def _like(authorid, storyid):
    q = Like.query.filter_by(liker_id=current_user.id, story_id=storyid)
    if q.first() is None:
        new_like = Like()
        new_like.liker_id = current_user.id
        new_like.story_id = storyid
        new_like.liked_id = authorid
        db.session.add(new_like)
        db.session.commit()
        message = ''
    else:
        message = 'You\'ve already liked this story!'
    return _stories(message)


@stories.route('/stories/write', methods=['GET'])
@login_required
def _write_story():
    form = StoryForm()
    # prendi parole dalla sessione
    figures = session['figures']
    return render_template("write_story.html", submit_url="http://127.0.0.1:5000/stories/submit", form=form,
                           words=figures)


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
        if len(story_words) > 200:  # global variable
            result = 'Your story is too long'
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

    return render_template("write_story.html", submit_url='http://127.0.0.1:5000/stories/submit', form=form,
                           result=result)
