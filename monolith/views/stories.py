from flask import Blueprint, redirect, render_template, request, jsonify
from monolith.database import db, Story, Like
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm

stories = Blueprint('stories', __name__)

@stories.route('/stories')
def _stories(message=''):
    allstories = db.session.query(Story)
    return render_template("stories.html", message=message, stories=allstories, like_it_url="http://127.0.0.1:5000/stories/like/")


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

# Open a story functionality (1.8)
@stories.route('/stories/<storyid>', methods=['GET'])
def _open_story(storyid):
    story_result = Story.query.filter_by(id=storyid).first()
    if story_result is not None:
        # Dovrò chiamare il servizio di Jacopo
        rolled_dice = ['parola1', 'parola2', 'parola3', 'parola4', 'parola5', 'parola6']
        return render_template('story.html', exists=True, story=story_result, dice=rolled_dice)
    else:
        return render_template('story.html', exists=False)