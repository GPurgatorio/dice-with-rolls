from flask import Blueprint, redirect, render_template, request
from monolith.database import db, User
from monolith.auth import admin_required, current_user
from monolith.forms import UserForm

users = Blueprint('users', __name__)


@users.route('/users')
def _users():
    usrs = db.session.query(User)
    return render_template("users.html", users=usrs)


@users.route('/users/create', methods=['POST'])
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


@users.route('/users/<int:userid>', methods=['GET'])
def _wall(userid):

    user_info = User.query.filter_by(id=userid).first()
    if user_info is not None:
        return render_template('wall.html', exists = True, user_info=user_info)
    else:
        return render_template('wall.html', exists = False)
