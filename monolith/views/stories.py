import string
from flask import Blueprint, redirect, render_template, request, abort, session, make_response
from monolith.database import db, Story, Like
from monolith.views.dice import _roll_dice
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import StoryForm

stories = Blueprint('stories', __name__)


@stories.route('/stories')
def _stories(message='', status=200):
    allstories = db.session.query(Story)
    return make_response(render_template("stories.html", message=message, stories=allstories,
                                         like_it_url="http://127.0.0.1:5000/stories/like/"), status)


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


@stories.route('/stories/write', methods=['GET', 'POST'])
@login_required
def _write_story(message='', status=200):
    if 'figures' not in session:
        return _roll_dice()

    figures = session['figures']
    form = StoryForm()

    if 'POST' == request.method:
        if form.validate_on_submit():

            dice_figures = session['figures'].copy()
            trans = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
            new_s = form['text'].data.translate(trans)
            story_words = new_s.split(' ')

            for w in story_words:
                if w in dice_figures:
                    dice_figures.remove(w)
                    if not dice_figures:
                        break

            if len(dice_figures) > 0:
                message = 'Your story doesn\'t contain all the words. Missing:'
                status = 400
                for w in dice_figures:
                    message += w + ' '
            else:
                message = 'Your story is a valid one! It has been published'
                status = 201
                new_story = Story()
                new_story.author_id = current_user.id
                new_story.figures = '#'.join(session['figures'])
                form.populate_obj(new_story)
                db.session.add(new_story)
                db.session.commit()
                session.pop('figures')
                return _stories(message=message, status=status)

    return make_response(
        render_template("write_story.html", submit_url="http://127.0.0.1:5000/stories/write", form=form,
                        words=figures, message=message), status)
