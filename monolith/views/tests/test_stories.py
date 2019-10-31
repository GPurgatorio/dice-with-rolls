from flask import session
import flask_testing
from flask_login import login_user, current_user

from monolith.app import app as my_app
from monolith.database import db, Story
from monolith.forms import LoginForm, StoryForm


class TestTemplateStories(flask_testing.TestCase):

    def create_app(self):
        my_app.config['LOGIN_DISABLED'] = True
        my_app.login_manager.init_app(my_app)
        return my_app

    def test_existing_story(self):
        self.client.get('/stories/1')
        self.assert_template_used('story.html')
        test_story = Story.query.filter_by(id=1).first()
        print('L\'oggetto da db: \n')
        print('User ID: ' + str(test_story.id))
        print('Author: ' + str(test_story.author))
        print('Date: ' + str(test_story.date))
        self.assertEqual(self.get_context_variable('story'), test_story)


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
