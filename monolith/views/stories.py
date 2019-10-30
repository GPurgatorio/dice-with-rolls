import datetime

from flask import Blueprint, redirect, render_template, request, abort, session
from sqlalchemy import func, desc, asc

from monolith.database import db, Story
from flask import Blueprint, redirect, render_template, request
from monolith.database import db, Story, Reaction, ReactionCatalogue, Counter, User
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
from monolith.forms import UserForm, StoryForm
from monolith.urls import SUBMIT_URL, REACTION_URL, LATEST_URL, RANGE_URL
                         login_required, fresh_login_required)
from sqlalchemy import and_
from monolith.forms import UserForm

stories = Blueprint('stories', __name__)

class StoryWithReaction:
    def __init__(self, _story):
        self.story = _story
        self.reactions ={}



@stories.route('/stories')
def _stories(message=''):
    context_vars = {"message": message, "stories": allstories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL}
    allstories = db.session.query(Story).all()
    stories = []
    for story in allstories:
        new_StoryWithReaction = StoryWithReaction(story)
        list_of_reactions = db.session.query(Counter.reaction_type_id).join(ReactionCatalogue).all()

        for item in list_of_reactions:
            new_StoryWithReaction.reactions[item.caption] = item.counter

        stories.append(new_StoryWithReaction)

    return render_template("stories.html", message=message, stories=stories, reaction_url="http://127.0.0.1:5000/stories/reaction")


@stories.route('/stories/react/<story_id>/<reaction_caption>', methods=['GET', 'POST'])
@login_required
def _reaction(reaction_caption, story_id):
    #Retrieve all reactions with a specific user_id ad story_id
    old_reaction = Reaction.query.filter(and_(Reaction.reactor_id == current_user.id, Reaction.story_id== story_id, Reaction.marked != 2)).first()
    #Retrieve the id of the reaction
    reaction_type_id = ReactionCatalogue.query.filter_by(reaction_caption=reaction_caption).first().reaction_id
    #Retrieve if present the user's last reaction about the same story
    if old_reaction is None:
        new_reaction = Reaction()
        new_reaction.reactor_id = current_user.id
        new_reaction.story_id = story_id
        new_reaction.reaction_type_id = reaction_type_id
        new_reaction.marked=0
        db.session.add(new_reaction)
        db.session.commit()
        message = ''
    else:
        if old_reaction.reaction_type_id == reaction_type_id:
            message = 'You have already reacted this story'
            return _stories(message)
        else:

            if old_reaction.marked == 0:
                old_reaction.reaction_type_id = reaction_type_id
            elif old_reaction.marked == 1:
                old_reaction.marked = 2
                new_reaction = Reaction()
                new_reaction.reactor_id = current_user.id
                new_reaction.story_id = story_id
                new_reaction.marked = 0
                new_reaction.reaction_type_id = reaction_type_id
                db.session.add(new_reaction)
                db.session.commit()

    db.session.commit()

    return _stories('')


@stories.route('/stories/delete_reaction/<story_id>')
@login_required
def _delete_reaction(story_id):
    reaction = Reaction.query.filter_by(liker_id=current_user.id, story_id=story_id, reaction_type_id=0 or 1).first()

    if reaction.marked == 0:
        Reaction.query.filter_by(liker_id=current_user.id, story_id=story_id).delete()
    elif reaction.marked == 1:
        reaction.marked = 2

    return _stories('Reaction eliminata')
