import flask_testing
import datetime
from flask import Flask
from monolith.views import blueprints
from monolith.auth import login_manager

from monolith.app import app as my_app
from monolith.forms import LoginForm, StoryForm
from monolith.database import Story, User, db, ReactionCatalogue
from monolith.urls import RANGE_URL, LATEST_URL


class TestTemplateStories(flask_testing.TestCase):
    app = None

    # First thing called
    def create_app(self):
        global app
        app = Flask(__name__, template_folder='../../templates')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
        app.config['SECRET_KEY'] = 'ANOTHER ONE'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['WTF_CSRF_ENABLED'] = False

        # app.config['LOGIN_DISABLED'] = True
        # cache config
        app.config['CACHE_TYPE'] = 'simple'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300

        for bp in blueprints:
            app.register_blueprint(bp)
            bp.app = app

        db.init_app(app)
        login_manager.init_app(app)
        db.create_all(app=app)

        return app

    # Set up database for testing here
    def setUp(self) -> None:
        with app.app_context():
            # Create admin user (if not present)
            q = db.session.query(User).filter(User.email == 'example@example.com')
            user = q.first()
            if user is None:
                example = User()
                example.firstname = 'Admin'
                example.lastname = 'Admin'
                example.email = 'example@example.com'
                example.dateofbirth = datetime.datetime(2020, 10, 5)
                example.is_admin = True
                example.set_password('admin')
                db.session.add(example)
                db.session.commit()

            # Create non admin user (if not present)
            q = db.session.query(User).filter(User.email == 'abc@abc.com')
            user = q.first()
            if user is None:
                example = User()
                example.firstname = 'Abc'
                example.lastname = 'Abc'
                example.email = 'abc@abc.com'
                example.dateofbirth = datetime.datetime(2010, 10, 5)
                example.is_admin = False
                example.set_password('abc')
                db.session.add(example)
                db.session.commit()

            # Create another non admin user (if not present)
            q = db.session.query(User).filter(User.email == 'nini@nini.com')
            user = q.first()
            if user is None:
                example = User()
                example.firstname = 'Nini'
                example.lastname = 'Nini'
                example.email = 'nini@nini.com'
                example.dateofbirth = datetime.datetime(2010, 10, 7)
                example.is_admin = False
                example.set_password('nini')
                db.session.add(example)
                db.session.commit()

            # Create an account that will have 0 stories
            q = db.session.query(User).filter(User.email == 'no@stories.com')
            user = q.first()
            if user is None:
                example = User()
                example.firstname = 'No'
                example.lastname = 'Stories'
                example.email = 'no@stories.com'
                example.dateofbirth = datetime.datetime(2010, 10, 5)
                example.is_admin = False
                example.set_password('no')
                db.session.add(example)
                db.session.commit()

            # Create the first story, default from teacher's code
            q = db.session.query(Story).filter(Story.id == 1)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'Trial story of example admin user :)'
                example.author_id = 1
                example.figures = 'example#admin'
                example.date = datetime.datetime.strptime('2019-10-20', '%Y-%m-%d')
                db.session.add(example)
                db.session.commit()

            # Create a story that shouldn't be seen in /latest
            q = db.session.query(Story).filter(Story.id == 2)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'Old story (dont see this in /latest)'
                example.date = datetime.datetime.strptime('2019-10-10', '%Y-%m-%d')
                example.likes = 420
                example.author_id = 2
                example.figures = 'example#abc'
                db.session.add(example)
                db.session.commit()

            # Create a story that should be seen in /latest
            q = db.session.query(Story).filter(Story.id == 3)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'You should see this one in /latest'
                example.date = datetime.datetime.strptime('2019-10-13', '%Y-%m-%d')
                example.likes = 3
                example.author_id = 2
                example.figures = 'example#abc'
                db.session.add(example)
                db.session.commit()

            # Random story from a non-admin user
            q = db.session.query(Story).filter(Story.id == 4)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'story from not admin'
                example.date = datetime.datetime.strptime('2018-12-30', '%Y-%m-%d')
                example.likes = 100
                example.author_id = 3
                example.figures = 'example#nini'
                db.session.add(example)
                db.session.commit()

            # Create a very old story for range searches purpose
            q = db.session.query(Story).filter(Story.id == 5)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'very old story (11 11 2011)'
                example.date = datetime.datetime.strptime('2011-11-11', '%Y-%m-%d')
                example.likes = 2
                example.author_id = 3
                example.figures = 'example#nini'
                example.date = datetime.datetime(2011, 11, 11)
                db.session.add(example)
                db.session.commit()

            # Add two reactions (Like and Dislike)
            like_reaction = ReactionCatalogue()
            like_reaction.reaction_caption = 'Like'
            dislike_reaction = ReactionCatalogue()
            dislike_reaction.reaction_caption = 'Dislike'
            love_reaction = ReactionCatalogue()
            love_reaction.reaction_caption = 'Love'
            db.session.add(like_reaction)
            db.session.add(dislike_reaction)
            db.session.add(love_reaction)
            db.session.commit()

        payload = {'email': 'example@example.com',
                   'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

    # Executed at end of each test
    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()

    def test_existing_story(self):
        self.client.get('/stories/1')
        self.assert_template_used('story.html')
        test_story = Story.query.filter_by(id=1).first()
        self.assertEqual(self.get_context_variable('story'), test_story)
        # Ordered reactions
        reactions = [('Dislike', 0), ('Like', 0), ('Love', 0)]
        self.assert_context('reactions', reactions)

    def test_non_existing_story(self):
        self.client.get('/stories/50')
        self.assert_template_used('story.html')
        self.assertEqual(self.get_context_variable('exists'), False)
        
    def test_latest_story(self):
        # Testing that the total number of users is higher or equal than the number of latest stories per user
        self.client.get(LATEST_URL)
        self.assert_template_used('stories.html')
        num_users = len(db.session.query(User).all())
        self.assertLessEqual(self.get_context_variable('stories').rowcount, num_users)

    def test_range_story(self):
      
        # Testing range without parameters
        self.client.get(RANGE_URL)
        self.assert_template_used('stories.html')
        all_stories = db.session.query(Story).all()
        self.assertEqual(self.get_context_variable('stories').all(), all_stories)


        # Testing range with only one parameter (begin)
        self.client.get(RANGE_URL + '?begin=2013-10-10')
        d = datetime.datetime.strptime('2013-10-10', '%Y-%m-%d')
        req_stories = Story.query.filter(Story.date >= d).all()
        self.assertEqual(self.get_context_variable('stories').all(), req_stories)

        # Testing range with only one parameter (end)
        self.client.get(RANGE_URL + '?end=2013-10-10')
        e = datetime.datetime.strptime('2013-10-10', '%Y-%m-%d')
        req_stories = Story.query.filter(Story.date <= e).all()
        self.assertEqual(self.get_context_variable('stories').all(), req_stories)


        # Testing range with begin date > end date
        self.client.get(RANGE_URL + '?begin=2012-12-12&end=2011-10-10')
        self.assertEqual(self.get_context_variable('message'), 'Begin date cannot be higher than End date')

        # Testing range (valid request)
        d = datetime.datetime.strptime('2012-10-15', '%Y-%m-%d')
        e = datetime.datetime.strptime('2020-10-10', '%Y-%m-%d')
        self.client.get(RANGE_URL + '?begin=2012-10-15&end=2020-10-10')
        req_stories = Story.query.filter(Story.date >= d).filter(Story.date <= e).all()
        self.assertEqual(self.get_context_variable('stories').all(), req_stories)

class TestStories(flask_testing.TestCase):

    def create_app(self):
        my_app.config['WTF_CSRF_ENABLED'] = False
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_stories(self):
        self.client.get('/stories')
        self.assert_200(self.client.get('/stories'))
        self.assert_template_used('stories.html')

    def test_write_story(self):
        payload = {'email': 'example@example.com',
                   'password': 'admin'}

        form = LoginForm(data=payload)

        self.client.post('/users/login', data=form.data, follow_redirects=True)

        # test write without rolling dice
        self.assert_redirects(self.client.get('/stories/new/write'), '/')
        self.client.get('/stories/new/write', follow_redirects=True)
        self.assert_template_used('index.html')

        # test write with right session
        with self.client.session_transaction() as session:
            session['figures'] = ['beer', 'cat', 'dog']
        self.assert200(self.client.get('/stories/new/write'))
        self.assert_template_used('write_story.html')

        # test write with invalid story
        payload = {'text': 'my cat is drinking a gin tonic with my neighbour\'s dog'}
        form = StoryForm(data=payload)
        response = self.client.post('/stories/new/write', data=form.data)
        self.assert400(response)
        self.assert_template_used('write_story.html')
        self.assert_context('message', 'Your story doesn\'t contain all the words. Missing: beer ')

        # test write story with valide one
        payload1 = {'text': 'my cat is drinking a beer with my neighbour\'s dog'}
        form1 = StoryForm(data=payload1)
        response = self.client.post('/stories/new/write', data=form1.data, follow_redirects=True)
        self.assert_status(response, 200)
        self.assert_template_used('stories.html')

        # test write story with draft id
        draft = Story()
        draft.author_id = 1
        draft.figures = 'dog#cat#beer'
        draft.text = 'halloween bye bye'
        draft.is_draft = True
        db.session.add(draft)
        db.session.commit()
        draft_db = Story.query.filter(Story.figures == 'dog#cat#beer', Story.text == 'halloween bye bye',
                                      Story.author_id == 1).first()

        url = '/stories/new/write/' + str(draft_db.id)
        response = self.client.get(url)
        self.assert200(response)
        self.assert_template_used('write_story.html')

        response = self.client.post(url, data=form1.data, follow_redirects=True)
        self.assert200(response)
        self.assert_template_used('stories.html')
        self.assertEqual(draft_db.is_draft, False)
        self.assertEqual(draft_db.text, 'my cat is drinking a beer with my neighbour\'s dog')

        # test write story with invalid draft (not yours)
        response = self.client.post(url, data=form1.data)
        self.assert_status(response, 302)
        # test write story with invalid draft (not draft)
        response = self.client.post(url, data=form1.data)
        self.assert_status(response, 302)
        self.assert_template_used('stories.html')
