import string
from monolith.views.dice import _roll_dice
from flask import Blueprint, redirect, render_template, request, abort, session, make_response, url_for
from monolith.database import db, Story
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm, StoryForm

stories = Blueprint('stories', __name__)


@stories.route('/stories')
def _stories(message='', status=200):
    allstories = db.session.query(Story)
    return make_response(render_template("stories.html", message=message, stories=allstories,
                                         like_it_url="http://127.0.0.1:5000/stories/like/"), status)


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
            print('ciao')
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
