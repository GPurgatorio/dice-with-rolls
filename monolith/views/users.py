import re
from datetime import date

from flask import Blueprint, redirect, render_template, request
from flask import flash, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from monolith.auth import current_user
from monolith.database import Follower
from monolith.database import db, User, Story
from monolith.forms import UserForm

users = Blueprint('users', __name__)


@users.route('/users')
def _users():
    usrs = db.session.query(User)
    return render_template("users.html", users=usrs)


@users.route('/users/create', methods=['GET', 'POST'])
def _create_user():
    form = UserForm()
    message = ""
    if request.method == 'POST':

        if form.validate_on_submit():
            # check if the email already exists
            email = form.data['email']
            user = db.session.query(User).filter(User.email == email).first()
            if user is None:
                # check if date of birth < today
                dateofbirth = form.data['dateofbirth']
                if dateofbirth < date.today():
                    new_user = User()
                    form.populate_obj(new_user)
                    new_user.set_password(form.password.data)  # pw should be hashed with some salt
                    db.session.add(new_user)
                    db.session.commit()
                    return redirect('/users')
                else:
                    message = "Wrong date of birth."
            else:
                message = "The email address is already being used."

    return render_template('create_user.html', form=form, message=message)


@users.route('/users/<int:userid>', methods=['GET'])
def _wall(userid):
    statistics = list()
    my_wall = False

    # Get the list of all stories
    all_stories = Story.query.filter_by(author_id=userid)

    # Total number of stories
    tot_num_stories = Story.query.filter_by(author_id=userid).count()

    # Total number of reactions
    tot_num_reactions = 0

    for story in all_stories:
        result = list(db.engine.execute("SELECT sum(counter) as num_reactions "
                                        "FROM counter "
                                        "WHERE story_id = {} "
                                        "GROUP BY story_id".format(story.id)))

        num_react = re.sub(r'\D', '', str(result))

        if not num_react:
            num_react = 0
        else:
            num_react = int(re.sub(r'\D', '', str(result)))

        tot_num_reactions += num_react

    # If I open my wall 
    if current_user is not None and hasattr(current_user, 'id') and current_user.id == userid:
        user_info = current_user
        my_wall = True

        # Average number of dice per story
        avg_dice = 0.0
        tot_num_dice = 0

        for story in all_stories:
            rolled_dice = story.figures.split('#')
            tot_num_dice += len(rolled_dice)

        # Avg of reactions / num of stories
        if tot_num_stories == 0:
            avg = 0.0
        else:
            avg = round(tot_num_reactions / tot_num_stories, 2)
            avg_dice = round(tot_num_dice / tot_num_stories, 2)

        statistics.append(('avg_reactions', avg))
        statistics.append(('num_reactions', tot_num_reactions))
        statistics.append(('num_stories', tot_num_stories))
        statistics.append(('avg_dice', avg_dice))

    # If I'm a generic user that open a wall
    else:
        user_info = User.query.filter_by(id=userid).first()

        if user_info is not None:
            statistics.append(('num_reactions', tot_num_reactions))
            statistics.append(('num_stories', tot_num_stories))
        else:
            return render_template('wall.html', not_found=True)

    return render_template('wall.html', my_wall=my_wall, user_info=user_info, stats=statistics)


@users.route('/users/<int:id_user>/follow', methods=['POST'])
@login_required
def _follow_user(id_user):
    if id_user == current_user.id:
        flash("You can't follow yourself")
        return redirect(url_for('users._wall', userid=id_user))
    if not _check_user_existence(id_user):
        flash("Storyteller doesn't exist")
        return redirect(url_for('users._wall', userid=current_user.id))
    if _check_follower_existence(current_user.id, id_user):
        flash("You already follow this storyteller")
        return redirect(url_for('users._wall', userid=id_user))

    new_follower = Follower()
    new_follower.follower_id = current_user.id
    new_follower.followed_id = id_user
    try:
        db.session.add(new_follower)
        # TODO This update could be done with celery
        db.session.query(User).filter_by(id=id_user).update({'follower_counter': User.follower_counter + 1})
        db.session.commit()

    except IntegrityError:
        flash("Error")
        return redirect(url_for('users._wall', userid=id_user))

    flash('Followed')
    return redirect(url_for('users._wall', userid=id_user))


# TODO Check if user follows the user
@users.route('/users/<int:id_user>/unfollow', methods=['POST'])
@login_required
def _unfollow_user(id_user):
    if id_user == current_user.id:
        flash("You can't unfollow yourself")
        return redirect(url_for('users._wall', userid=id_user))
    if not _check_user_existence(id_user):
        flash("Storyteller doesn't exist")
        return redirect(url_for('users._wall', userid=current_user.id))
    if not _check_follower_existence(current_user.id, id_user):
        flash("You should follow him first")
        return redirect(url_for('users._wall', userid=id_user))

    Follower.query.filter_by(follower_id=current_user.id, followed_id=id_user).delete()
    # TODO This update could be done with celery
    db.session.query(User).filter_by(id=id_user).update({'follower_counter': User.follower_counter - 1})
    db.session.commit()
    flash('Unfollowed')
    return redirect(url_for('users._wall', userid=id_user))


def _check_user_existence(id_user):
    followed_user = db.session.query(User).filter(User.id == id_user)
    print("CHECK_USER_QUERY" + str(followed_user))
    """if followed_user.first() is None:
        return False
    else:
        return True"""
    return followed_user.first() is not None


def _check_follower_existence(follower_id, followed_id):
    print("FOLLOWER_ID " + str(follower_id) + " FOLLOWED_ID " + str(followed_id))
    follower = db.session.query(Follower).filter_by(follower_id=follower_id, followed_id=followed_id)
    print("CHECK_FOLLOWER_QUERY" + str(follower))
    """if follower.first() is None:
        return False
    else:
        return True"""

    return follower.first() is not None
