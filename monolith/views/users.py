from flask import Blueprint, redirect, render_template, request, flash, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from monolith.database import db, User, Follower
from flask import Blueprint, redirect, render_template, request
from monolith.database import db, User, Story, Counter
from monolith.auth import admin_required, current_user
from monolith.forms import UserForm

users = Blueprint('users', __name__)


@users.route('/users')
def _users():
    usrs = db.session.query(User)
    return render_template("users.html", users=usrs)


@users.route('/users/create', methods=['GET', 'POST'])
def _create_user():
    form = UserForm()
    if request.method == 'POST':

        if form.validate_on_submit():
            new_user = User()
            form.populate_obj(new_user)
            new_user.set_password(form.password.data)  # pw should be hashed with some salt
            db.session.add(new_user)
            db.session.commit()
            return redirect('/users')

    return render_template('create_user.html', form=form)


@users.route('/users/<int:userid>')
def _wall(userid):
    user_info = None

    if current_user is not None and hasattr(current_user, 'id'):
        user_info = current_user

        # Get the list of all stories
        all_stories = Story.query.filter_by(author_id=userid)

        # Total number of stories
        tot_num_stories = Story.query.filter_by(author_id=userid).count()

        # Total number of reactions
        tot_num_reactions = 0

        for story in all_stories:
            tot_num_reactions += Counter.query.filter_by(story_id=story.id).count()

        # Average number of dice per story
        avg_dice = 0.0
        tot_num_dice = 0

        for story in all_stories:
            rolled_dice = story.figures.split('#')
            tot_num_dice += len(rolled_dice)

        # Avg of reactions / num of stories
        if tot_num_stories == 0:
            avg = 0.0
            avg_dice = 0.0
        else:
            avg = tot_num_reactions / tot_num_stories
            avg_dice = tot_num_dice / tot_num_stories

        stats = [('avg_reactions', avg), ('num_reactions', tot_num_reactions), ('num_stories', tot_num_stories),
                 ('avg_dice', avg_dice)]

    return render_template('wall.html', user_info=user_info, stats=stats)


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

    except IntegrityError as e:
        flash("Error")
        return redirect(url_for('users._wall', userid=id_user))

    flash('Followed')
    return redirect(url_for('users._wall', userid=id_user))


# TODO Check if he/she follow the user
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
    if followed_user.first() is None:
        return False
    else:
        return True


def _check_follower_existence(follower_id, followed_id):
    print("FOLLOWER_ID " + str(follower_id) + " FOLLOWED_ID " + str(followed_id))
    follower = db.session.query(Follower).filter_by(follower_id=follower_id, followed_id=followed_id)
    print("CHECK_FOLLOWER_QUERY" + str(follower))
    if follower.first() is None:
        return False
    else:
        return True
