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
    text = db.Column(db.Text(1000)) # around 200 (English) words 
    date = db.Column(db.DateTime)
    # define foreign key
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship('User', foreign_keys='Story.author_id')

    def __init__(self, *args, **kw):
        super(Story, self).__init__(*args, **kw)
        self.date = dt.datetime.now()

class Reaction_catalogue(db.Model):
    __tablename__ = 'reaction_catalogue'

    reaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reaction_caption = db.Column(db.Text(20))


class Reaction(db.Model):
    __tablename__ = 'reaction'

    reactor_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    reactor = relationship('User', foreign_keys='Reaction.reactor_id')

    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), primary_key=True)
    author = relationship('Story', foreign_keys='Reaction.story_id')

    reaction_type_id = db.Column(db.Integer, db.ForeignKey('reaction_catalogue.reaction_id'))
    reaction_type = relationship('Reaction_catalogue', foreign_keys='Reaction.reaction_type_id')

    marked = db.Column(db.Boolean, default=False)  # True iff it has been counted in Story.likes


class Counter(db.Model):
    __tablename__ = 'counter'

    reaction_type_id = db.Column(db.Integer, db.ForeignKey('reaction_catalogue.reaction_id'), primary_key=True)
    reaction_type = relationship('Reaction_catalogue', foreign_keys='Counter.reaction_type_id')

    story_id = db.Column(db.Integer , db.ForeignKey('story.id', primary_key=True))
    story = relationship('Story', foreign_keys='Counter.story_id')

    counter = db.Column(db.Integer, default=0)







