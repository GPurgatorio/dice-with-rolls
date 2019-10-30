from flask import Blueprint, redirect, render_template, request, flash, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from monolith.database import db, User, Follower
from monolith.auth import admin_required, current_user
from monolith.forms import UserForm

users = Blueprint('users', __name__)


@users.route('/users')
@login_required
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


@users.route('/users/<userid>')
def _wall(userid):
    user_info = None
    if current_user is not None and hasattr(current_user, 'id'):
        user_info = current_user
    return render_template('wall.html', user_info=user_info)


# TODO Change methods to POST
# TODO This method should not be callable outside the id_user's wall (?) so we could not check for id_user existence
# Uniqueness is checked by the database
@users.route('/users/<int:id_user>/follow', methods=['GET'])
@login_required
def _follow_user(id_user):
    if _check_follower_existence(current_user.id, id_user):
        flash("You already follow this storyteller", 'error')
        return redirect(url_for('users._wall', id_user=id_user))
    if id_user == current_user.id:
        flash("You can't follow yourself", 'error')
        return redirect(url_for('users._wall', id_user=id_user))
    if not _check_user_existence(id_user):
        # TODO This should redirect somewhere else because id_user doesn't exists
        flash("User doesn't exist", 'error')
        return redirect(url_for('users._wall', id_user=id_user))

    new_follower = Follower()
    new_follower.follower_id = current_user.id
    new_follower.followed_id = id_user
    try:
        db.session.add(new_follower)
        # TODO This update could be done with celery
        db.session.query(User).filter_by(id=id_user).update({'follower_counter': User.follower_counter + 1})
        db.session.commit()

    except IntegrityError as e:
        # TODO This exception is also thrown if he/she already follow
        flash("Error", 'error')
        return redirect(url_for('users._wall', id_user=id_user))
        # print("FOLLOWED " + new_follower.followed_id + "FOLLOWER " + new_follower.follower_id)
    flash('Followed')
    return redirect(url_for('users._wall', id_user=id_user))


# TODO Check if he/she follow the user
@users.route('/users/<int:id_user>/unfollow', methods=['GET'])
@login_required
def _unfollow_user(id_user):
    if not _check_follower_existence(current_user.id, id_user):
        flash("You should follow him first", 'error')
        return redirect(url_for('users._wall', id_user=id_user))
    if id_user == current_user.id:
        flash("You can't unfollow yourself", 'error')
        return redirect(url_for('users._wall', id_user=id_user))
    if not _check_user_existence(id_user):
        flash("User doesn't exist", 'error')
        return redirect(url_for('users._wall', id_user=id_user))
    Follower.query.filter_by(follower_id=current_user.id, followed_id=id_user).delete()
    # TODO This update could be done with celery
    db.session.query(User).filter_by(id=id_user).update({'follower_counter': User.follower_counter - 1})
    db.session.commit()
    flash('Unfollowed')
    return redirect(url_for('users._wall', id_user=id_user))


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
