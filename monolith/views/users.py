from flask import Blueprint, redirect, render_template, request
from monolith.database import db, User
from monolith.auth import admin_required, current_user
from monolith.forms import UserForm

users = Blueprint('users', __name__)


@users.route('/users')
def _users():
    usrs = db.session.query(User)
    return render_template("users.html", users=usrs)


@users.route('/users/create', methods=['GET', 'POST'])
def create_user():
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
			user_info=current_user
		return render_template('wall.html', user_info=user_info)
