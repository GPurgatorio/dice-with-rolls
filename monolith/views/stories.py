from random import randint
import datetime
import itertools
import re
import string

from flask import Blueprint, redirect, render_template, request, abort, session, make_response, url_for
from flask import session
from flask_login import (current_user, login_required)
from sqlalchemy import and_

from monolith.database import db, Story, Reaction, ReactionCatalogue, Counter
from monolith.forms import StoryForm
from monolith.urls import SUBMIT_URL, REACTION_URL, LATEST_URL, RANGE_URL, SETTINGS_URL, RANDOM_URL


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
                    "range_url": RANGE_URL, "random_recent_url": RANDOM_URL}

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


# Gets the last story for each registered user
@stories.route('/stories/latest', methods=['GET'])
def _latest(message=''):
    listed_stories = db.engine.execute(
        "SELECT * FROM story s1 "
        "WHERE s1.date = (SELECT MAX (s2.date) FROM story s2 WHERE s1.author_id == s2.author_id) "
        "ORDER BY s1.author_id")

    context_vars = {"message": message, "stories": listed_stories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL, "random_recent_url": RANDOM_URL}
    return render_template('stories.html', **context_vars)


# Searches for stories that were made in a specific range of time [begin_date, end_date]
@stories.route('/stories/range', methods=['GET'])
def _range(message=''):
    # Get the two parameters
    begin = request.args.get('begin')
    end = request.args.get('end')

    # Construct begin_date and end_date (given or default)
    try:
        if begin and len(begin) > 0:
            begin_date = datetime.datetime.strptime(begin, '%Y-%m-%d')
        else:
            begin_date = datetime.datetime.min
        if end and len(end) > 0:
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            # Here .replace is needed because of solar/legal hour!
            # Stories are written at time X in db, and searched at time X-1
            end_date = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)
    except ValueError:
        # return redirect(url_for('stories._stories'))      da cambiare con flash etc
        return render_template('stories.html', message='Wrong URL parameters.')
    if begin_date > end_date:
        return render_template('stories.html', message='Begin date cannot be higher than End date')

    listed_stories = db.session.query(Story).filter(Story.date >= begin_date).filter(Story.date <= end_date)
    context_vars = {"message": message, "stories": listed_stories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL, "random_recent_url": RANDOM_URL}
    return render_template('stories.html', **context_vars)


# Open a story functionality (1.8)
@stories.route('/stories/<int:id_story>', methods=['GET'])
def _open_story(id_story):
    story = Story.query.filter_by(id=id_story).first()

    if story is not None:
        # Splitting the names of figures
        rolled_dice = story.figures.split('#')
        
        # Get all the reactions for that story
        all_reactions = list(db.engine.execute("SELECT reaction_caption FROM reaction_catalogue ORDER BY reaction_caption"))
        query = "SELECT reaction_caption, counter as num_story_reactions FROM counter c, reaction_catalogue r WHERE reaction_type_id = reaction_id AND story_id = " + str(id_story) + " ORDER BY reaction_caption"
        story_reactions = list(db.engine.execute(query))
        num_story_reactions = Counter.query.filter_by(story_id=id_story).join(ReactionCatalogue).count()
        num_reactions = ReactionCatalogue.query.count()

        # Create tuples of counter per reaction
        list_tuples = list()
        reactions_counters = list()

        # Generate tuples (reaction, counter)
        if num_reactions != 0 and num_story_reactions != 0:
            for combination in itertools.zip_longest(all_reactions, story_reactions):
                list_tuples.append(combination)

            for i in range(0, num_reactions):
                reaction = str(list_tuples[i][0]).replace('(', '').replace(')', '').replace(',', '').replace('\'', '')
                counter = re.sub('\D', '', str(list_tuples[i][1]))
                reactions_counters.append((reaction, counter))

        else:
            for i in range(0, num_reactions):
                reaction = str(all_reactions[i]).replace('(', '').replace(')', '').replace(',', '').replace('\'', '')
                counter = 0
                reactions_counters.append((reaction, counter))

        return render_template('story.html', exists=True, story=story, rolled_dice=rolled_dice, reactions=reactions_counters)
      else:
        return render_template('story.html', exists=False)


@stories.route('/stories/new/write', defaults={'id_story': None}, methods=['GET', 'POST'])
@stories.route('/stories/new/write/<int:id_story>', methods=['GET', 'POST'])
@login_required
def _write_story(id_story=None, message='', status=200):
    form = StoryForm()
    submit_url = "http://127.0.0.1:5000/stories/new/write"

    if id_story is not None:
        story = Story.query.filter(Story.id == id_story).first()
        if story is not None and story.author_id == current_user.id and story.is_draft:
            form.text = story.text
            session['figures'] = story.figures.split('#')  # questo va sempre aggiornato? pensaci
            submit_url = "http://127.0.0.1:5000/stories/new/write/" + str(id_story)
        else:
            message = 'Request is invalid, check if you are the author of the story and it is still a draft'
            return redirect(url_for('stories._stories'))
    else:
        if 'figures' not in session:
            # redirect to home
            return redirect('/', code=302)

    figures = session['figures']

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
                message = 'Your story doesn\'t contain all the words. Missing: '
                status = 400
                for w in dice_figures:
                    message += w + ' '
            else:
                message = 'Your story is a valid one! It has been published'
                status = 201
                if id_story is not None:
                    print(id_story)
                    old_story = Story.query.filter_by(id=id_story).first()
                    old_story.text = form['text'].data
                    old_story.is_draft = False
                else:
                    new_story = Story()
                    new_story.author_id = current_user.id
                    new_story.figures = '#'.join(session['figures'])
                    new_story.is_draft = False
                    form.populate_obj(new_story)
                    db.session.add(new_story)
                    db.session.commit()
                session.pop('figures')
                return redirect(url_for('stories._stories'))
                # redirect(url_for('stories._stories', message=message, status=status), code=status)

    return make_response(
        render_template("write_story.html", submit_url=submit_url, form=form,
                        words=figures, message=message), status)


@stories.route('/stories/random', methods=['GET'])
def _random_story():
    # get all the stories written in the last three days 
    begin = (datetime.datetime.now() - datetime.timedelta(3)).date()
    recent_stories = db.session.query(Story).filter(Story.date >= begin).all()
    # pick a random story from them
    if len(recent_stories)==0:
        message = "Oops, there are no recent stories!"
        context_vars = {"message": message, "reaction_url": REACTION_URL, "latest_url": LATEST_URL, 
                        "range_url": RANGE_URL, "random_recent_url": RANDOM_URL}
        return render_template("stories.html", **context_vars)
    else:
        pos = randint(0, len(recent_stories)-1)
        return _open_story(recent_stories[pos].id)