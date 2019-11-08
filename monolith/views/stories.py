import datetime
import itertools
import re
import string
from random import randint

from flask import Blueprint, redirect, render_template, request, make_response, url_for, flash
from flask import session
from flask_login import (current_user, login_required)
from sqlalchemy import and_

from monolith.database import db, Story, Reaction, ReactionCatalogue, Counter, User
from monolith.forms import StoryForm
from monolith.urls import *

stories = Blueprint('stories', __name__)


@stories.route('/stories')
def _stories():
    all_stories = db.session.query(Story).filter_by(is_draft=False).all()

    context_vars = {"stories": all_stories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL, "random_recent_url": RANDOM_URL,
                    "story_url": READ_URL, "wall_url": USERS_URL}

    return render_template("stories.html", **context_vars)


@stories.route('/stories/<story_id>/react/<reaction_caption>', methods=['GET', 'POST'])
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
    else:
        if old_reaction.reaction_type_id == reaction_type_id:
            reaction = Reaction.query.filter(Reaction.reactor_id == current_user.id,
                                             Reaction.story_id == story_id,
                                             Reaction.marked != 2).first()
            if reaction.marked == 0:
                Reaction.query.filter_by(reactor_id=current_user.id, story_id=story_id).delete()

            if reaction.marked == 1:
                reaction.marked = 2

            db.session.commit()
            flash('Reaction successfully deleted! (Updating ... )')
            return redirect(url_for('stories._open_story', id_story=story_id))
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
    flash('Reaction successfully added! (Updating ... )')

    return redirect(url_for('stories._open_story', id_story=story_id))


# Gets the last NON-draft story for each registered user
@stories.route('/stories/latest', methods=['GET'])
def _latest():
    listed_stories = db.engine.execute(
        "SELECT * FROM story s1 "
        "WHERE s1.date = (SELECT MAX (s2.date) FROM story s2 WHERE s1.author_id == s2.author_id "
        "AND s2.is_draft == 0) "
        "ORDER BY s1.author_id").fetchall()

    context_vars = {"stories": listed_stories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL, "random_recent_url": RANDOM_URL}
    return render_template('stories.html', **context_vars)


# Searches for stories that were made in a specific range of time
@stories.route('/stories/range', methods=['GET'])
def _range():
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
    # If a strptime fails getting the date, it means at least one of the parameters was invalid
    except ValueError:
        flash('Wrong URL parameters.', 'error')
        return redirect(url_for('stories._stories'))

    # If dates were valid, I still have to check if the request is a valid one
    if begin_date > end_date:
        flash('Begin date cannot be higher than End date.', 'error')
        return redirect(url_for('stories._stories'))

    # Returns all the NON-draft stories that are between the requested dates
    listed_stories = db.session.query(Story).filter(Story.date >= begin_date).filter(Story.date <= end_date).filter(
        Story.is_draft == False)

    context_vars = {"stories": listed_stories,
                    "reaction_url": REACTION_URL, "latest_url": LATEST_URL,
                    "range_url": RANGE_URL, "random_recent_url": RANDOM_URL}
    return render_template('stories.html', **context_vars)


# Open a story functionality (1.8)
@stories.route('/stories/<int:id_story>', methods=['GET'])
def _open_story(id_story):
    q = db.session.query(Story, User).filter(Story.id == id_story).join(User).first()

    if q is not None:
        story = q[0]
        user = q[1]
        #  Splitting the names of figures
        rolled_dice = story.figures.split('#')

        rolled_dice = rolled_dice[1:-1]

        # Get author name of that story
        author = list(db.engine.execute("SELECT firstname, lastname FROM user join story on user.id = author_id WHERE story.id = " + str(id_story)))
        
        # Get all the reactions for that story
        all_reactions = list(db.engine.execute("SELECT reaction_caption FROM reaction_catalogue ORDER BY reaction_caption"))
        query = "SELECT reaction_caption, counter as num_story_reactions FROM counter c, reaction_catalogue r WHERE " \
                "reaction_type_id = reaction_id AND story_id = " + str(id_story) + " ORDER BY reaction_caption "

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
                counter = re.sub(r'\D', '', str(list_tuples[i][1]))
                if not counter:
                    counter = 0
                else:
                    counter = int(counter)

                reactions_counters.append((reaction, counter))
        else:
            for reaction in all_reactions:
                reactions_counters.append((reaction.reaction_caption, 0))

        print(reactions_counters)
        return render_template('story.html', exists=True, story=story, react_url=REACTION_URL,
                               user=user, rolled_dice=rolled_dice, reactions=reactions_counters)
    else:
        return render_template('story.html', exists=False)


# Get the form to write a new story or continue a draft
# Publish the story or save as draft
@stories.route('/stories/new/write', defaults={'id_story': None}, methods=['GET', 'POST'])
@stories.route('/stories/new/write/<int:id_story>', methods=['GET'])
@login_required
def _write_story(id_story=None, message='', status=200):
    form = StoryForm()
    submit_url = WRITE_URL

    # Setting session to modify draft
    if 'GET' == request.method and id_story is not None:
        story = Story.query.filter(Story.id == id_story).first()
        if story is not None and story.author_id == current_user.id and story.is_draft:
            form.text.data = story.text
            session['figures'] = story.figures.split('#')
            session['figures'] = session['figures'][1:-1]
            session['id_story'] = story.id
        else:
            flash('Request is invalid, check if you are the author of the story and it is still a draft', 'error')
            return redirect(url_for('users._user_drafts', id_user=current_user.id))

    # Check if there are the words to write the story
    if 'figures' not in session:
        flash('Request is invalid, you need to set a story before', 'error')
        return redirect(url_for('home.index'))

    elif 'POST' == request.method:
        if form.validate_on_submit():
            draft = bool(int(form.as_draft.data))
            if draft:
                if 'id_story' in session:
                    # Update a draft
                    db.session.query(Story).filter_by(id=session['id_story']).update({'text': form.text.data,
                                                                                      'date': datetime.datetime.now()})
                    db.session.commit()
                    session.pop('id_story')
                else:
                    # Save new story as draft
                    new_story = Story()
                    new_story.author_id = current_user.id
                    new_story.figures = '#' + '#'.join(session['figures']) + '#'
                    new_story.is_draft = True
                    form.populate_obj(new_story)
                    db.session.add(new_story)
                    db.session.commit()
                session.pop('figures')
                return redirect(url_for('users._user_drafts', id_user=current_user.id))
            else:
                # Check validity
                dice_figures = session['figures'].copy()
                trans = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
                new_s = form['text'].data.translate(trans).lower()
                story_words = new_s.split()
                for w in story_words:
                    if w in dice_figures:
                        dice_figures.remove(w)
                        if not dice_figures:
                            break
                if len(dice_figures) > 0:
                    status = 400
                    message = 'Your story doesn\'t contain all the words. Missing: '
                    for w in dice_figures:
                        message += w + ' '
                else:
                    if 'id_story' in session:
                        # Publish a draft
                        date_format = "%Y %m %d %H:%M"
                        date = datetime.datetime.strptime(datetime.datetime.now().strftime(date_format), date_format)
                        db.session.query(Story).filter_by(id=session['id_story']).update(
                            {'text': form.text.data, 'date': date, 'is_draft': False})
                        db.session.commit()
                        session.pop('id_story')
                    else:
                        # Publish a new story
                        new_story = Story()
                        new_story.author_id = current_user.id
                        new_story.figures = '#' + '#'.join(session['figures']) + '#'
                        new_story.is_draft = False
                        form.populate_obj(new_story)
                        db.session.add(new_story)
                        db.session.commit()
                    session.pop('figures')
                    flash('Your story is a valid one! It has been published')
                    return redirect(url_for('users._user_stories', id_user=current_user.id, _external=True))
    return make_response(
        render_template("write_story.html", submit_url=submit_url, form=form,
                        words=session['figures'], message=message), status)


@stories.route('/stories/delete/<int:id_story>', methods=['POST'])
@login_required
def _manage_stories(id_story):
    story_to_delete = Story.query.filter(Story.id == id_story)
    if story_to_delete.first().author_id != current_user.id:
        flash("Cannot delete other user's story", 'error')
    else:

        Reaction.query.filter(Reaction.story_id == id_story).delete()
        Counter.query.filter(Counter.story_id == id_story).delete()
        story_to_delete.delete()
        db.session.commit()

    return redirect(url_for("home.index"))


# Get a random story written by other users in the last three days
@stories.route('/stories/random', methods=['GET'])
def _random_story():
    # get all the stories written in the last three days by other users
    begin = (datetime.datetime.now() - datetime.timedelta(3)).date()
    if current_user is not None and hasattr(current_user, 'id'):
        q = db.session.query(Story).filter(Story.date >= begin,
                                           Story.author_id != current_user.id,
                                           Story.is_draft == False)
    else:
        q = db.session.query(Story).filter(Story.date >= begin, Story.is_draft == False)
    recent_stories = q.all()
    # pick a random story from them
    if len(recent_stories) == 0:
        flash("Oops, there are no recent stories by other users!")
        return redirect(url_for('stories._stories'))
    else:
        pos = randint(0, len(recent_stories) - 1)
        return redirect(url_for("stories._open_story", id_story=recent_stories[pos].id))
