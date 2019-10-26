import unittest
from monolith.tests.test_utils import client, login, logout

class TestStories(unittest.TestCase):
    def test_story_write(self):
        app = client()
        login(app, "example@example.com", "admin")
        assert app.get('/stories').status_code == 200


