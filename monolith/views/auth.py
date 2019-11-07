from flask import Blueprint, render_template, redirect, request, flash
from flask_login import (login_user, logout_user)

from monolith.database import db, User
from monolith.forms import LoginForm
from monolith.urls import HOME_URL

auth = Blueprint('auth', __name__)


@auth.route('/users/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            email, password = form.data['email'], form.data['password']
            q = db.session.query(User).filter(User.email == email)
            user = q.first()
            if user is None:
                flash('This email does not exist.', 'error')
            elif user is not None and not user.authenticate(password):
                flash('Password is incorrect.', 'error')
            else:
                login_user(user)
                return redirect('/')

    return render_template('login.html', form=form, home_url=HOME_URL)


@auth.route("/users/logout", methods=['POST'])
def logout():
    logout_user()
    return redirect('/')
