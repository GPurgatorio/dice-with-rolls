# encoding: utf8
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from sqlalchemy.orm import relationship
import datetime as dt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Unicode(128), nullable=False)
    firstname = db.Column(db.Unicode(128))
    lastname = db.Column(db.Unicode(128))
    password = db.Column(db.Unicode(128))
    dateofbirth = db.Column(db.DateTime)
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


class Story(db.Model):
    __tablename__ = 'story'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text(1000))  # around 200 (English) words
    date = db.Column(db.DateTime)
    # likes = db.Column(db.Integer)  # will store the number of likes, periodically updated in background
    # define foreign key 
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship('User', foreign_keys='Story.author_id')

    def __init__(self, *args, **kw):
        super(Story, self).__init__(*args, **kw)
        self.date = dt.datetime.now()


class ReactionInfo(db.Model):
    __tablename__ = 'reaction_info'

    reacter_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    reacter = relationship('User', foreign_keys='ReactionInfo.reacter_id')

    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), primary_key=True)
    author = relationship('Story', foreign_keys='ReactionInfo.story_id')

    reacted_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # TODO: duplicated ?
    reacted = relationship('User', foreign_keys='ReactionInfo.reacted_id')

    reaction_id = db.Column(db.Integer, db.ForeignKey('reaction.id'))
    reaction = relationship('Reaction', foreign_keys='ReactionInfo.reaction_id')

    marked = db.Column(db.Boolean, default=False)  # True iff it has been counted in Story.likes


class Counter(db.Model):
    __tablename__ = 'counter'
    # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # big fun name
    reaction_id = db.Column(db.Integer, db.ForeignKey('reaction.id'), primary_key=True)
    reaction = relationship('Reaction', foreign_keys='Counter.reaction_id')

    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), primary_key=True)
    story = relationship('Story', foreign_keys='Counter.story_id')
    # will store the number of reactions with reaction_id and for story_id, periodically updated in background
    counter = db.Column(db.Integer)


class Reaction(db.Model):
    __tablename__ = 'reaction'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text(200))
