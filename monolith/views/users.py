from flask import Blueprint, redirect, render_template, request, flash, abort, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from monolith.database import db, User, Follower
from monolith.auth import admin_required
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


# TODO That's a mock, change it
@users.route('/users/<int:id_user>', methods=['GET'])
def _user_wall(id_user):
    return render_template('my_wall.html')


# TODO Change methods to POST
# TODO This method should not be callable outside the id_user's wall (?) so we could not check for id_user existence
# Uniqueness is checked by the database
@users.route('/users/<int:id_user>/follow', methods=['GET'])
@login_required
def _follow_user(id_user):
    followed_user = db.session.query(User).filter(User.id == id_user)
    # print(followed_user)
    if followed_user.first() is None:
        flash("User doesn't exist", 'error')
        return redirect(url_for('users._user_wall', id_user=id_user))
        # return redirect(url_for('/users/' + str(id_user), message="NON ESISTE NEL DB"))
    new_follower = Follower()
    new_follower.follower_id = current_user.id
    new_follower.followed_id = id_user
    try:
        db.session.add(new_follower)
        db.session.commit()
    except IntegrityError as e:
        flash("You can't follow yourself!", 'error')
        return redirect(url_for('users._user_wall', id_user=id_user))
        # print("FOLLOWED " + new_follower.followed_id + "FOLLOWER " + new_follower.follower_id)
    flash('Followed')
    return redirect(url_for('users._user_wall', id_user=id_user))
