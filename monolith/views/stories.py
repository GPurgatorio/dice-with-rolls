import datetime

from flask import Blueprint, render_template, request
from flask import session
from flask_login import (current_user, login_required)
from sqlalchemy import and_

from monolith.database import db, Story, Reaction, ReactionCatalogue, Counter
from monolith.forms import StoryForm
from monolith.urls import SUBMIT_URL, REACTION_URL, LATEST_URL, RANGE_URL

stories = Blueprint('stories', __name__)


class StoryWithReaction:
    def __init__(self, _story):
        self.story = _story
        self.reactions = {}

@stories.route('/stories')
def _stories(message=''):
    allstories = db.session.query(Story).all()
    listed_stories = []
    for story in allstories:
        new_story_with_reaction = StoryWithReaction(story)
        list_of_reactions = db.session.query(Counter.reaction_type_id).join(ReactionCatalogue).all()

        for item in list_of_reactions:
            new_story_with_reaction.reactions[item.caption] = item.counter
        listed_stories.append(new_story_with_reaction)

    context_vars = {"message": message, "stories": allstories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL}

    return render_template("stories.html", **context_vars)


@stories.route('/stories/react/<story_id>/<reaction_caption>', methods=['GET', 'POST'])
@login_required
def _reaction(reaction_caption, story_id):
    # Retrieve all reactions with a specific user_id ad story_id
    old_reaction = Reaction.query.filter(and_(Reaction.reactor_id == current_user.id,
                                              Reaction.story_id == story_id,
                                              Reaction.marked != 2)).first()
    # Retrieve the id of the reaction
    reaction_type_id = ReactionCatalogue.query.filter_by(reaction_caption=reaction_caption).first().reaction_id
    # Retrieve if present the user's last reaction about the same story
    if old_reaction is None:
        new_reaction = Reaction()
        new_reaction.reactor_id = current_user.id
        new_reaction.story_id = story_id
        new_reaction.reaction_type_id = reaction_type_id
        new_reaction.marked = 0
        db.session.add(new_reaction)
        db.session.commit()
        # message = ''
    else:
        if old_reaction.reaction_type_id == reaction_type_id:
            message = 'You have already reacted to this story!'
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

    return _stories('Reaction successfully deleted!')


@stories.route('/stories/latest', methods=['GET'])
def _latest(message=''):
    listed_stories = db.engine.execute(
        "SELECT * FROM story s1 "
        "WHERE s1.date = (SELECT MAX (s2.date) FROM story s2 WHERE s1.author_id == s2.author_id) "
        "ORDER BY s1.author_id")

    context_vars = {"message": message, "stories": listed_stories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL}
    return render_template('stories.html', **context_vars)


@stories.route('/stories/range', methods=['GET'])
def _range(message=''):
    begin = request.args.get('begin')
    end = request.args.get('end')

    try:
        if begin and len(begin) > 0:
            begin_date = datetime.datetime.strptime(begin, '%Y-%m-%d')
        else:
            begin_date = datetime.datetime.min
        if end and len(end) > 0:
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
        else:
            end_date = datetime.datetime.utcnow()
    except ValueError:
        # return redirect(url_for('stories._stories'))      da cambiare con flash etc
        return render_template('stories.html', message='Wrong URL parameters.')
    if begin_date > end_date:
        return render_template('stories.html', message='Begin date cannot be higher than End date')
    listed_stories = db.session.query(Story).filter(Story.date >= begin_date).filter(Story.date <= end_date)
    context_vars = {"message": message, "stories": listed_stories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL}
    return render_template('stories.html', **context_vars)


# Open a story functionality (1.8)
@stories.route('/stories/<int:id_story>', methods=['GET'])
def _open_story(id_story):
    # Get the story object from database
    story = Story.query.filter_by(id=id_story).first()
    if story is not None:
        rolled_dice = story.figures.split('#')
        # TODO : aggiornare per le reactions
        context_vars = {"exists": True, "story": story,
                        "rolled_dice": rolled_dice}
        return render_template('story.html', **context_vars)
    else:
        return render_template('story.html', exists=False)


@stories.route('/stories/new/write', methods=['GET', 'POST'])
@login_required
def _write_story(message=''):
    form = StoryForm()
    # prendi parole dalla sessione
    figures = session['figures']
    context_vars = {"message": message, "submit_url": SUBMIT_URL,
                    "form": form, "words": figures}
    return render_template("write_story.html", **context_vars)


@stories.route('/stories/new/submit', methods=['POST'])
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
                result = 'Your story is a valid one! It has been published.'
                db.session.add(new_story)
                db.session.commit()
                return _stories(message=result)
            else:
                result = 'Your story doesn\'t contain all the words!'

    return _write_story(message=result)
