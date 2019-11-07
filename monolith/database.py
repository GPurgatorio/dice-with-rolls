# encoding: utf8
import datetime as dt

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Unicode(128), nullable=False)
    firstname = db.Column(db.Unicode(128))
    lastname = db.Column(db.Unicode(128))
    password = db.Column(db.Unicode(128))
    dateofbirth = db.Column(db.DateTime)

    follower_counter = db.Column(db.Integer, default=0, )

    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_anonymous = False

    def __init__(self, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self._authenticated = False

    def set_password(self, password):
        self.password = generate_password_hash(password)

    @property
    def is_authenticated(self):
        return self._authenticated

    def authenticate(self, password):
        checked = check_password_hash(self.password, password)
        self._authenticated = checked
        return self._authenticated

    def get_id(self):
        return self.id

    __table_args__ = (CheckConstraint(follower_counter >= 0, name='follower_counter_positive'), {})


class Follower(db.Model):
    __tablename__ = 'follower'

    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    follower = relationship('User', foreign_keys='Follower.follower_id')

    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed = relationship('User', foreign_keys='Follower.followed_id')

    __table_args__ = (CheckConstraint(followed_id != follower_id, name='check_follow_myself'), {})


class Story(db.Model):
    __tablename__ = 'story'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text(1000))  # around 200 (English) words
    date = db.Column(db.DateTime)
    figures = db.Column(db.Unicode(128))
    # define foreign key
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship('User', foreign_keys='Story.author_id')
    is_draft = db.Column(db.Boolean, default=True)

    def __init__(self, *args, **kw):
        super(Story, self).__init__(*args, **kw)
        date_format = "%Y %m %d %H:%M"
        self.date = dt.datetime.strptime(dt.datetime.now().strftime(date_format), date_format)
        print(self.date)


class ReactionCatalogue(db.Model):
    __tablename__ = 'reaction_catalogue'

    reaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reaction_caption = db.Column(db.Text(20))


class Reaction(db.Model):
    __tablename__ = 'reaction'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    reactor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reactor = relationship('User', foreign_keys='Reaction.reactor_id')

    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    author = relationship('Story', foreign_keys='Reaction.story_id')

    reaction_type_id = db.Column(db.Integer, db.ForeignKey('reaction_catalogue.reaction_id'))
    reaction_type = relationship('ReactionCatalogue', foreign_keys='Reaction.reaction_type_id')

    marked = db.Column(db.Integer, default=0)  # True iff it has been counted in Story.likes


class Counter(db.Model):
    __tablename__ = 'counter'

    reaction_type_id = db.Column(db.Integer, db.ForeignKey('reaction_catalogue.reaction_id'), primary_key=True)
    reaction_type = relationship('ReactionCatalogue', foreign_keys='Counter.reaction_type_id')

    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), primary_key=True)
    story = relationship('Story', foreign_keys='Counter.story_id')

    counter = db.Column(db.Integer, default=0)
