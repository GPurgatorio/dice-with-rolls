from flask import Blueprint, redirect, render_template, request
from monolith.database import db, User
from monolith.auth import admin_required, current_user
from monolith.forms import UserForm

users = Blueprint('users', __name__)


@users.route('/users')
def _users():
    usrs = db.session.query(User)
    return render_template("users.html", users=usrs)


@users.route('/create_user', methods=['GET', 'POST'])
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


@users.route('/my_wall')
def _my_wall():
    if current_user is not None and hasattr(current_user, 'id'):
        user_info = db.session.query(User).filter(User.id == current_user.id).one()
    else:
        user_info = None
    return render_template('my_wall.html', user_info=user_info)