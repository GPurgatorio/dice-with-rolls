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
    user_info = None
    statistics = list()
    my_wall = False
    
    # If I open my wall 
    if current_user is not None and hasattr(current_user, 'id') and current_user.id == userid:
        user_info = current_user
        my_wall = True

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
            avg = round(tot_num_reactions / tot_num_stories, 2)
            avg_dice = round(tot_num_dice / tot_num_stories, 2)

        statistics.append(('avg_reactions', avg))
        statistics.append(('num_reactions', tot_num_reactions))
        statistics.append(('num_stories', tot_num_stories))
        statistics.append(('avg_dice', avg_dice))

    # If I'm a generic user that open a wall
    else:
        user_info = User.query.filter_by(id=userid).first()

        # Get the list of all stories
        all_stories = Story.query.filter_by(author_id=userid)
        
        # Total number of stories
        tot_num_stories = Story.query.filter_by(author_id=userid).count()
        
        # Total number of reactions
        tot_num_reactions = 0

        for story in all_stories:
            tot_num_reactions += Counter.query.filter_by(story_id=story.id).count()
            rolled_dice = story.figures.split('#')

        statistics.append(('num_reactions', tot_num_reactions))
        statistics.append(('num_stories', tot_num_stories))


    return render_template('wall.html', my_wall=my_wall, user_info=user_info, stats=statistics)