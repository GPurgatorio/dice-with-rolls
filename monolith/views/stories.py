from flask import Blueprint, redirect, render_template, request
from monolith.database import db, Story, Reaction, Reaction_catalogue, Counter
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm

stories = Blueprint('stories', __name__)


@stories.route('/stories')
def _stories(message=''):
    allstories = db.session.query(Story)
    return render_template("stories.html", message=message, stories=allstories, reaction_url="http://127.0.0.1:5000/stories/reaction")


@stories.route('/stories/reaction/<story_id>/<reaction_caption>')
@login_required
def _reaction(reaction_caption, story_id):
    #Retrieve all reactions with a specific user_id ad story_id
    reactions = Reaction.query.filter_by(reactor_id=current_user.id, story_id=story_id)
    #Retrieve the id of the reaction
    reaction_type_id = Reaction_catalogue.query.filter_by(reaction_caption=reaction_caption).first().reaction_id
    #Retrieve the counter for a specific reaction of a story
    counter = Counter.query.filter_by(story_id= story_id, reaction_type_id=reaction_type_id)
    #Retrieve if present the user's last reaction about the same story
    old_reaction = reactions.first()
    if old_reaction is None:
        new_reaction = Reaction()
        new_reaction.reactor_id = current_user.id
        new_reaction.story_id = story_id
        new_reaction.reaction_type_id = reaction_type_id
        db.session.add(new_reaction)
        db.session.commit()
        message = ''
    else:
        if old_reaction.reaction_type_id == reaction_type_id:
            message = 'You have already reacted this story'
            return _stories(message)
        else:
            #If the user tries to insert a different reaction for the same story, change the old reaction type,
            #decrement the old reaction type's couter and then increment the new type's one
            old_reaction_type = old_reaction.reaction_type_id
            old_reaction.reaction_type_id = reaction_type_id
            Counter.query.filter_by(story_id=story_id, reaction_type_id=old_reaction_type).first().counter -= 1
            db.session.commit()

    current_counter = counter.first()
    if current_counter is None:
        new_counter = Counter()
        new_counter.reaction_type_id = reaction_type_id
        new_counter.reactor_id = current_user.id
        new_counter.story_id = story_id
        new_counter.counter = 1
        db.session.add(new_counter)
    else:
        current_counter.counter += 1

    db.session.commit()

    return _stories('')


@stories.route('/stories/delete_reaction/<story_id>/<reaction_type>')
@login_required
def _delete_reaction(story_id, reaction_type):
    Reaction.query.filter_by(liker_id=current_user.id, story_id=story_id).delete()
    counter = Counter.query.filter(story_id= story_id, reaction_type_id=reaction_type).first()
    counter.counter -= 1

    return _stories('Reaction eliminata')
