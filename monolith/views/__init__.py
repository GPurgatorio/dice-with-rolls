from .auth import auth
from .dice import dice
from .home import home
from .search import search
from .stories import stories
from .users import users

blueprints = [home, auth, users, stories, dice, search]
