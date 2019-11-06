import datetime

import flask_testing

from monolith.app import create_app
from monolith.database import Story, User, db, ReactionCatalogue, Counter
from monolith.forms import LoginForm, StoryForm
from monolith.urls import *


class TestTemplateStories(flask_testing.TestCase):
    app = None

    # First thing called
    def create_app(self):
        global app
        app = create_app(database=TEST_DB)
        return app

    # Set up database for testing here
    def setUp(self) -> None:
        with app.app_context():
            # Create admin user
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            db.session.add(example)
            db.session.commit()

            # Create non admin user
            example = User()
            example.firstname = 'Abc'
            example.lastname = 'Abc'
            example.email = 'abc@abc.com'
            example.dateofbirth = datetime.datetime(2010, 10, 5)
            example.is_admin = False
            example.set_password('abc')
            db.session.add(example)
            db.session.commit()

            # Create another non admin user
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
            example = Story()
            example.text = 'Trial story of example admin user :)'
            example.author_id = 1
            example.figures = '#example#admin#'
            example.date = datetime.datetime.strptime('2019-10-20', '%Y-%m-%d')
            db.session.add(example)
            db.session.commit()

            # Create a story that shouldn't be seen in /latest
            example = Story()
            example.text = 'Old story (dont see this in /latest)'
            example.date = datetime.datetime.strptime('2019-10-10', '%Y-%m-%d')
            example.likes = 420
            example.author_id = 2
            example.figures = '#example#abc#'
            db.session.add(example)
            db.session.commit()

            # Create a story that should be seen in /latest
            example = Story()
            example.text = 'You should see this one in /latest'
            example.date = datetime.datetime.strptime('2019-10-13', '%Y-%m-%d')
            example.likes = 3
            example.author_id = 2
            example.figures = '#example#abc#'
            db.session.add(example)
            db.session.commit()

            # Random story from a non-admin user
            example = Story()
            example.text = 'story from not admin'
            example.date = datetime.datetime.strptime('2018-12-30', '%Y-%m-%d')
            example.likes = 100
            example.author_id = 3
            example.figures = '#example#nini#'
            db.session.add(example)
            db.session.commit()

            # Create a very old story for range searches purpose
            example = Story()
            example.text = 'very old story (11 11 2011)'
            example.date = datetime.datetime.strptime('2011-11-11', '%Y-%m-%d')
            example.likes = 2
            example.author_id = 3
            example.figures = '#example#nini#'
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

            # login
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

        # Add reactions for user 1
        like = Counter()
        like.reaction_type_id = 1
        like.story_id = 1
        like.counter = 23
        dislike = Counter()
        dislike.reaction_type_id = 2
        dislike.story_id = 1
        dislike.counter = 5
        db.session.add(like)
        db.session.add(dislike)
        db.session.commit()

        # Test new statistics
        self.client.get('/stories/1')
        self.assert_template_used('story.html')
        test_story = Story.query.filter_by(id=1).first()
        self.assertEqual(self.get_context_variable('story'), test_story)
        # Ordered reactions
        reactions = [('Dislike', 5), ('Like', 23), ('Love', 0)]
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
        self.assert_message_flashed('Begin date cannot be higher than End date', 'error')

        # Testing wrong url parameters
        self.client.get(RANGE_URL + '?begin=abc&end=abc')
        self.assert_message_flashed('Wrong URL parameters.', 'error')

        # Testing range (valid request)
        d = datetime.datetime.strptime('2012-10-15', '%Y-%m-%d')
        e = datetime.datetime.strptime('2020-10-10', '%Y-%m-%d')
        self.client.get(RANGE_URL + '?begin=2012-10-15&end=2020-10-10')
        req_stories = Story.query.filter(Story.date >= d).filter(Story.date <= e).all()
        self.assertEqual(self.get_context_variable('stories').all(), req_stories)


class TestStories(flask_testing.TestCase):
    app = None

    # First thing called
    def create_app(self):
        global app
        app = create_app(database=TEST_DB)
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

            # Create the first story, default from teacher's code
            q = db.session.query(Story).filter(Story.id == 1)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'Trial story of example admin user :)'
                example.author_id = 1
                example.figures = '#example#admin#'
                example.is_draft = False
                db.session.add(example)
                db.session.commit()

            # Create a story of a different user
            q = db.session.query(Story).filter(Story.id == 2)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'You won\'t modify this story'
                example.author_id = 2
                example.figures = '#modify#story#'
                example.is_draft = False
                db.session.add(example)
                db.session.commit()

            # Create a draft for the logged user
            q = db.session.query(Story).filter(Story.id == 3)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'This is an example of draft'
                example.author_id = 1
                example.figures = '#example#draft#'
                example.is_draft = True
                db.session.add(example)
                db.session.commit()

            # Create a draft of a different user
            q = db.session.query(Story).filter(Story.id == 4)
            story = q.first()
            if story is None:
                example = Story()
                example.text = 'This is an example of draft that you can\'t modify'
                example.date = datetime.datetime.strptime('2018-12-30', '%Y-%m-%d')
                example.author_id = 2
                example.figures = '#example#draft#'
                example.is_draft = True
                db.session.add(example)
                db.session.commit()

            payload = {'email': 'example@example.com', 'password': 'admin'}

            form = LoginForm(data=payload)

            self.client.post('/users/login', data=form.data, follow_redirects=True)

    # Executed at end of each test
    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()

    def test_write_story(self):

        # Testing writing without rolling dice
        response = self.client.get(WRITE_URL)
        self.assert_redirects(response, HOME_URL)
        self.client.get(WRITE_URL, follow_redirects=False)
        self.assert_template_used('index.html')

        # Testing writing of a valid draft story
        response = self.client.get(WRITE_URL+'/3')
        self.assert200(response)
        self.assert_template_used('write_story.html')
        self.assert_context('words', ['example', 'draft'])

        # Testing writing of other user's draft
        response = self.client.get(WRITE_URL + '/4')
        self.assert_redirects(response, 'http://127.0.0.1:5000/users/1/drafts')

        # Testing writing of an already published story
        response = self.client.get(WRITE_URL + '/1')
        self.assert_redirects(response, 'http://127.0.0.1:5000/users/1/drafts')

        # Testing writing of a new story with valid session
        with self.client.session_transaction() as session:
            session['figures'] = ['beer', 'cat', 'dog']
        response = self.client.get(WRITE_URL)
        self.assert200(response)
        self.assert_template_used('write_story.html')
        self.assert_context('words', ['beer', 'cat', 'dog'])

        # Testing publishing invalid story
        payload = {'text': 'my cat is drinking a gin tonic with my neighbour\'s dog', 'as_draft': '0'}
        form = StoryForm(data=payload)
        response = self.client.post('/stories/new/write', data=form.data)
        self.assert400(response)
        self.assert_template_used('write_story.html')
        self.assert_context('message', 'Your story doesn\'t contain all the words. Missing: beer ')

        # Testing publishing valid story
        payload1 = {'text': 'my cat is drinking a beer with my neighbour\'s dog', 'as_draft': '0'}
        form1 = StoryForm(data=payload1)
        response = self.client.post('/stories/new/write', data=form1.data)
        self.assertEqual(response.status_code, 302)
        self.assert_redirects(response, '/users/1/stories')

        # Testing saving a new story as draft
        with self.client.session_transaction() as session:
            session['figures'] = ['beer', 'cat', 'dog']
        payload2 = {'text': 'my cat is drinking', 'as_draft': '1'}
        form2 = StoryForm(data=payload2)
        response = self.client.post('/stories/new/write', data=form2.data)
        self.assertEqual(response.status_code, 302)
        self.assert_redirects(response, '/users/1/drafts')

        # Testing saving a draft again
        with self.client.session_transaction() as session:
            session['figures'] = ['beer', 'cat', 'dog']
            session['id_story'] = 6
        response = self.client.post('/stories/new/write', data=form2.data)
        self.assertEqual(response.status_code, 302)
        self.assert_redirects(response, '/users/1/drafts')
        q = db.session.query(Story).filter(Story.id == 7).first()
        self.assertEqual(q, None)

        # Testing publishing a draft story
        with self.client.session_transaction() as session:
            session['figures'] = ['beer', 'cat', 'dog']
            session['id_story'] = 6
        payload3 = {'text': 'my cat is drinking dog and beer', 'as_draft': '0'}
        form3 = StoryForm(data=payload3)
        response = self.client.post('/stories/new/write', data=form3.data)
        self.assertEqual(response.status_code, 302)
        self.assert_redirects(response, '/users/1/stories')
        q = db.session.query(Story).filter(Story.id == 7).first()
        self.assertEqual(q, None)
        q = db.session.query(Story).filter(Story.id == 6).first()
        self.assertEqual(q.is_draft, False)


class TestRandomRecentStory(flask_testing.TestCase):
    app = None

    # First thing called
    def create_app(self):
        global app
        app = create_app(database=TEST_DB)
        return app

    # Set up database for testing here
    def setUp(self) -> None:
        with app.app_context():

            # Create an user (if not present)
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

            # Create a not recent story
            example = Story()
            example.text = 'This is a story about the end of the world'
            example.date = datetime.datetime.strptime('2012-12-12', '%Y-%m-%d')
            example.author_id = 1
            example.figures = 'story#world'
            example.is_draft = False
            db.session.add(example)
            db.session.commit() 

            payload = {'email': 'example@example.com', 'password': 'admin'}

            form = LoginForm(data=payload)

            self.client.post('/users/login', data=form.data, follow_redirects=True)

        def test_random_recent_story(self):

            # No recent stories
            self.client.get('/stories/random')
            self.assert_template_used('stories.html')
            self.assert_message_flashed('Oops, there are no recent stories!')

            # Create a new recent story
            example = Story()
            example.text = 'This is a recent story'
            example.date = datetime.datetime.now()
            example.author_id = 1
            example.figures = 'story#recent'
            example.is_draft = False
            db.session.add(example)
            db.session.commit()

            # Get the only recent story
            response = self.client.get('/stories/random')
            self.assert_template_used('story.html')
            test_story = Story.query.filter_by(id=1).first()
            self.assertEqual(self.get_context_variable('story'), test_story)

